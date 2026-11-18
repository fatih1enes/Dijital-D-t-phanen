"""Main FastAPI application entry point for Dijital Kütüphane."""

import asyncio
import json
import os
import time
import webbrowser
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from starlette.middleware.sessions import SessionMiddleware

from app.auth import (
    AUTH_COOKIE_NAME,
    AUTH_STATE,
    _get_access_password,
    _is_allowed_origin,
    _is_local_host,
    _is_unprotected_remote_allowed,
)
from app.constants import (
    ALLOWED_ORIGINS,
    COOKIE_SECURE,
    SESSION_SECRET,
    STATIC_DIR,
    TEMPLATES_DIR,
    THUMBNAILS_DIR,
)
from app.database import init_db_schema
from app.logger import log_event, set_global_loop, set_ws_manager
from app.routers import (
    auth as auth_module,
)
from app.routers import (
    books as books_module,
)
from app.routers import (
    chat as chat_module,
)
from app.routers import (
    collections as collections_module,
)
from app.routers import (
    debate as debate_module,
)
from app.routers import (
    opds as opds_module,
)
from app.routers import (
    settings as settings_module,
)
from app.routers import (
    srs as srs_module,
)
from app.routers import (
    tasks as tasks_module,
)
from app.routers import (
    telegram as telegram_module,
)
from app.routers import (
    tts as tts_module,
)
from app.task_queue import TaskQueue
from app.websocket import ConnectionManager

# WebSocket Manager
ws_manager = ConnectionManager()
set_ws_manager(ws_manager)

# Allowed Origins are imported from app.constants


async def _init_lifespan_resources(app: FastAPI) -> asyncio.Task:
    """Initialize database, queues, and background services on application startup."""
    set_global_loop(asyncio.get_running_loop())
    await init_db_schema()

    # Recover any orphaned durable jobs left across past crashes
    from app.durable_queue import DurableTaskQueue
    from app.event_bus import event_bus

    app.state.event_bus = event_bus
    durable_queue = getattr(app.state, "durable_queue", None)
    if not durable_queue:
        durable_queue = DurableTaskQueue()
        app.state.durable_queue = durable_queue
    try:
        recovered = await durable_queue.recover_orphaned_jobs()
        if recovered > 0:
            log_event(
                "system",
                "INFO",
                f"Açılışta {recovered} adet yarım kalmış görev kurtarıldı.",
            )
    except Exception as d_err:
        log_event("system", "DEBUG", f"Orphan job recovery note: {d_err}")

    task_queue = getattr(app.state, "task_queue", None)
    if not task_queue:
        task_queue = TaskQueue()
        app.state.task_queue = task_queue

    if not hasattr(app.state, "background_tasks"):
        app.state.background_tasks = set()

    worker_task = asyncio.create_task(task_queue.worker_loop())

    # Check and log security status for external network access
    active_pwd = _get_access_password()
    from app.routers.settings import _get_local_ip

    local_ip = _get_local_ip()
    if not active_pwd:
        if _is_unprotected_remote_allowed():
            log_event(
                "security",
                "WARNING",
                "ACCESS_PASSWORD ayarlanmamış fakat ALLOW_UNPROTECTED_REMOTE_ACCESS aktif. Kütüphane uzaktan şifresiz erişime açıktır!",
            )
        else:
            log_event(
                "security",
                "INFO",
                f"ACCESS_PASSWORD henüz ayarlanmamış. Telefondan erişim için Ayarlar > Güvenlik sekmesinden şifre belirleyebilirsiniz (Ağ IP: http://{local_ip}:8000).",
            )
    else:
        log_event(
            "security",
            "INFO",
            f"ACCESS_PASSWORD aktif. Telefondan bağlantı adresi: http://{local_ip}:8000",
        )

    try:
        from app.services.watchfolder_service import watchfolder_service

        await watchfolder_service.start()
    except Exception as wf_start_err:
        log_event("watchfolder", "DEBUG", f"Watchfolder start warning: {wf_start_err}")

    return worker_task


async def _shutdown_lifespan_resources(app: FastAPI, worker_task: asyncio.Task) -> None:
    """Safely terminate background workers and release external connections on application shutdown."""
    try:
        from app.services.watchfolder_service import watchfolder_service

        await watchfolder_service.stop()
    except Exception as wf_err:
        log_event("system", "DEBUG", f"Watchfolder shutdown note: {wf_err}")

    worker_task.cancel()
    await asyncio.gather(worker_task, return_exceptions=True)
    log_event("system", "DEBUG", "Worker task cleanly terminated on shutdown")

    task_queue = getattr(app.state, "task_queue", None)
    if task_queue:
        try:
            await asyncio.to_thread(task_queue.shutdown, wait=True)
        except Exception as tq_err:
            log_event("system", "DEBUG", f"TaskQueue shutdown error: {tq_err}")

    try:
        from app.services.session_manager import book_session_manager

        await asyncio.to_thread(book_session_manager.close_all)
    except Exception as e:
        log_event("ai", "DEBUG", f"Session manager close_all error: {e}")

    try:
        from app.services.telegram_service import telegram_service

        if telegram_service._client and telegram_service._client.is_connected():
            await telegram_service._client.disconnect()
    except Exception as e:
        log_event("telegram", "DEBUG", f"Telegram disconnect during shutdown: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    worker_task = await _init_lifespan_resources(app)
    try:
        yield
    finally:
        await _shutdown_lifespan_resources(app, worker_task)


app = FastAPI(title="Digital Library API", lifespan=lifespan)
app.state.task_queue = None
app.state.background_tasks = set()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Centralized fallback exception handler ensuring clean JSON error responses."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None) or {},
        )
    log_event("security", "ERROR", f"Beklenmeyen sunucu hatası: {exc}", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "İç sunucu hatası oluştu. Lütfen sistem loglarını kontrol edin.",
            "error": str(exc) if os.environ.get("DEBUG") else None,
        },
    )


# FastAPICache initialization
FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


class SecurityHeadersASGIMiddleware:
    """Pure-ASGI security headers middleware (zero response body buffering for Range streaming)."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers") or [])
                existing = {k.lower() for k, _ in raw_headers}
                if b"x-content-type-options" not in existing:
                    raw_headers.append((b"x-content-type-options", b"nosniff"))
                if b"x-frame-options" not in existing:
                    raw_headers.append((b"x-frame-options", b"SAMEORIGIN"))
                if b"referrer-policy" not in existing:
                    raw_headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


class PasswordGateASGIMiddleware:
    """Pure-ASGI authentication gate preserving zero-copy streaming for authorized requests."""

    _PUBLIC_EXACT = frozenset({"/login", "/health", "/ready", "/sw.js", "/favicon.ico"})
    _PUBLIC_PREFIXES = ("/static", "/api/auth", "/opds", "/handoff")

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        if path in self._PUBLIC_EXACT or path.startswith(self._PUBLIC_PREFIXES):
            await self.app(scope, receive, send)
            return

        from app.auth import _is_access_allowed

        request = Request(scope, receive=receive)
        if not _is_access_allowed(request):
            accept = request.headers.get("accept", "")
            if "text/html" in accept:
                resp: Response = RedirectResponse(url="/login", status_code=303)
            else:
                resp = JSONResponse(status_code=401, content={"detail": "Authentication required"})
            await resp(scope, receive, send)
            return

        await self.app(scope, receive, send)


# Middleware registration (innermost -> outermost):
# CORSMiddleware -> SecurityHeaders -> SessionMiddleware -> PasswordGate -> Router
app.add_middleware(PasswordGateASGIMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=COOKIE_SECURE,
)
app.add_middleware(SecurityHeadersASGIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=[
        "Accept-Ranges",
        "Content-Range",
        "Content-Length",
        "ETag",
        "Content-Disposition",
    ],
)


# Static files and Templates
app.mount("/thumbnails", StaticFiles(directory=THUMBNAILS_DIR), name="thumbnails")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/sw.js", include_in_schema=False)
async def service_worker_root() -> Response:
    """Serve PWA Service Worker from root scope so it can control '/' and offline shell."""
    from fastapi.responses import FileResponse

    sw_path = os.path.join(STATIC_DIR, "sw.js")
    if not os.path.isfile(sw_path):
        raise HTTPException(status_code=404, detail="Service worker not found")
    return FileResponse(
        sw_path,
        media_type="application/javascript; charset=utf-8",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache, must-revalidate",
        },
    )


# HTML Page Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """Render the main library page."""
    return templates.TemplateResponse(request, "kutuphane.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Render login page."""
    return templates.TemplateResponse(request, "login.html")


@app.get("/reader/{file_hash}")
async def reader_page(request: Request, file_hash: str) -> RedirectResponse:
    """Redirect legacy reader URL to main library page."""
    return RedirectResponse(url="/", status_code=302)


@app.get("/workspace/{file_hash}")
async def workspace_page(request: Request, file_hash: str) -> RedirectResponse:
    """Redirect legacy workspace URL to main library page."""
    return RedirectResponse(url="/", status_code=302)


@app.get("/handoff/{token}")
async def redeem_handoff(request: Request, token: str) -> Response:
    """Redeem a valid handoff token, issue session credentials, and redirect to book workspace."""
    import secrets

    from app.auth import AUTH_STATE, _auth_lock, _cleanup_expired_tokens
    from app.constants import AUTH_COOKIE_NAME, COOKIE_SECURE
    from app.services.handoff_service import consume_handoff_token

    data = consume_handoff_token(token)
    if not data:
        log_event("security", "WARNING", "Invalid or expired handoff token redemption attempt")
        return RedirectResponse(url="/", status_code=302)

    auth_token = secrets.token_hex(32)
    _cleanup_expired_tokens()
    with _auth_lock:
        AUTH_STATE["valid_tokens"][auth_token] = time.time() + (60 * 60 * 24 * 30)

    target_url = f"/?open_book={data['file_hash']}&page={data['page_number']}"
    resp = RedirectResponse(url=target_url, status_code=302)
    resp.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=auth_token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
        max_age=60 * 60 * 24 * 30,
    )
    return resp


# Health & Readiness Probes
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Liveness probe for container orchestration and uptime monitoring."""
    return {"status": "ok", "timestamp": time.time()}


@app.get(
    "/ready",
    tags=["health"],
    responses={503: {"description": "Veritabanı veya alt sistem hazır değil"}},
)
async def readiness_check() -> dict:
    """Readiness probe checking database connectivity and core subsystems."""
    from app.database import get_db_context

    db_healthy = False
    try:
        async with get_db_context() as db:
            row = await (await db.conn.execute("SELECT 1")).fetchone()
            if row and row[0] == 1:
                db_healthy = True
    except Exception as e:
        log_event("system", "ERROR", f"Readiness database probe failed: {e}")

    if not db_healthy:
        raise HTTPException(
            status_code=503, detail={"status": "unhealthy", "database": "disconnected"}
        )

    return {"status": "ready", "database": "connected", "timestamp": time.time()}


def _is_valid_remote_token(ws_cookie: str) -> bool:
    """Validate remote auth token against active token registry."""
    from app.auth import _auth_lock

    if not ws_cookie:
        return False
    with _auth_lock:
        exp = AUTH_STATE["valid_tokens"].get(ws_cookie)
        if exp is None:
            return False
        if time.time() <= exp:
            return True
        AUTH_STATE["valid_tokens"].pop(ws_cookie, None)
        return False


def _is_local_websocket(websocket: WebSocket) -> bool:
    """Check if WebSocket physically originates from localhost, honoring TRUST_PROXY."""
    ws_host = websocket.client.host if websocket.client else ""
    if not _is_local_host(ws_host):
        return False
    trust_proxy = os.environ.get("TRUST_PROXY", "0").strip().lower() in ("1", "true", "yes")
    if trust_proxy:
        forwarded = websocket.headers.get("x-forwarded-for")
        if forwarded:
            first_hop = forwarded.split(",")[0].strip()
            return _is_local_host(first_hop)
    return True


async def _check_remote_websocket_auth(websocket: WebSocket, ws_host: str) -> bool:
    """Verify password protection and cookie token for remote WebSocket connections."""
    pwd = _get_access_password()
    if not pwd:
        if not _is_unprotected_remote_allowed():
            log_event(
                "security",
                "WARNING",
                "WebSocket rejected: Remote access without ACCESS_PASSWORD is prohibited",
                client_host=ws_host,
            )
            await websocket.close(code=1008)
            return False
        return True

    ws_cookie = websocket.cookies.get(AUTH_COOKIE_NAME, "")
    if not _is_valid_remote_token(ws_cookie):
        log_event(
            "security",
            "WARNING",
            "WebSocket auth rejected: Invalid or expired token",
            client_host=ws_host,
        )
        await websocket.close(code=1008)
        return False
    return True


async def _authenticate_websocket(websocket: WebSocket) -> bool:
    """Validate origin and authentication token for incoming WebSocket connection."""
    ws_host = websocket.client.host if websocket.client else ""
    ws_origin = websocket.headers.get("origin", "").strip()

    if ws_origin and not _is_allowed_origin(ws_origin, websocket, ALLOWED_ORIGINS):
        log_event(
            "security",
            "WARNING",
            "WebSocket origin rejected",
            origin=ws_origin,
            client_host=ws_host,
        )
        await websocket.close(code=1008)
        return False

    if not _is_local_websocket(websocket):
        return await _check_remote_websocket_auth(websocket, ws_host)
    return True


# WebSocket Route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint."""
    if not await _authenticate_websocket(websocket):
        return

    connected = await ws_manager.connect(websocket)
    if not connected:
        return

    try:
        while True:
            raw_msg = await websocket.receive_text()
            try:
                parsed = json.loads(raw_msg)
                if isinstance(parsed, dict) and parsed.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except (json.JSONDecodeError, UnicodeDecodeError) as parse_err:
                log_event("websocket", "DEBUG", f"Ignored non-json ws frame: {parse_err}")
    except WebSocketDisconnect:
        log_event("websocket", "DEBUG", "WebSocket client disconnected")
    except Exception as ws_err:
        log_event("websocket", "DEBUG", f"WebSocket closed with error: {ws_err}")
    finally:
        ws_manager.disconnect(websocket)


# Register Routers
app.include_router(auth_module.router)
app.include_router(books_module.router)
app.include_router(collections_module.router)
app.include_router(tasks_module.router)
app.include_router(chat_module.router)
app.include_router(settings_module.router)
app.include_router(telegram_module.router)
app.include_router(opds_module.router)
app.include_router(debate_module.router)
app.include_router(tts_module.router)
app.include_router(srs_module.router)


def open_browser() -> None:
    """Opens the library page in the default web browser."""
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    from threading import Timer

    import uvicorn

    if os.getenv("AUTO_OPEN_BROWSER", "True").lower() == "true":
        timer = Timer(1.5, open_browser)
        timer.daemon = True
        timer.start()

    server_host = os.getenv("HOST", "127.0.0.1")
    server_port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=server_host, port=server_port)
