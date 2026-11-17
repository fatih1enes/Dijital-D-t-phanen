"""Authentication router."""

import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

import app.auth as auth_mod
from app.constants import AUTH_COOKIE_NAME
from app.models import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_auth_helpers() -> tuple:
    return (
        auth_mod._is_local_request,
        auth_mod._get_access_password,
        auth_mod._is_unprotected_remote_allowed,
    )


@router.get("/status")
async def auth_status(request: Request) -> dict:
    """Return authentication status."""
    fn_local, fn_pwd, fn_unprot = _get_auth_helpers()
    is_local = fn_local(request)
    pwd = fn_pwd()
    unprotected_remote = fn_unprot()
    required = bool(not is_local and (bool(pwd) or not unprotected_remote))
    has_pwd = bool(pwd)

    authenticated = False
    if is_local or auth_mod._is_access_allowed(request):
        authenticated = True

    now_ts = time.time()
    client_host = auth_mod._get_client_host(request)
    locked = auth_mod._is_login_locked(client_host, now_ts)
    remaining_seconds = auth_mod._remaining_lock_seconds(client_host, now_ts) if locked else 0
    return {
        "required": required,
        "is_local": is_local,
        "authenticated": authenticated,
        "has_password": has_pwd,
        "locked": locked,
        "remaining_seconds": remaining_seconds,
    }


@router.post(
    "/login",
    responses={
        401: {"description": "Hatalı şifre"},
        403: {"description": "Erişim engellendi"},
        429: {"description": "Çok fazla deneme"},
    },
)
async def login(request: Request, payload: LoginRequest | None = None) -> JSONResponse:
    """Authenticate with password."""
    auth_mod._ensure_safe_request_origin(request)
    fn_local, fn_pwd, fn_unprot = _get_auth_helpers()
    is_local = fn_local(request)
    configured_pwd = fn_pwd()

    if not is_local and not configured_pwd and not fn_unprot():
        raise HTTPException(
            status_code=403,
            detail="Sunucuda ACCESS_PASSWORD belirlenmemiş. Güvenlik nedeniyle uzaktan erişim engellenmiştir.",
        )

    now = time.time()
    client_host = auth_mod._get_client_host(request)
    if auth_mod._is_login_locked(client_host, now):
        remaining = auth_mod._remaining_lock_seconds(client_host, now)
        raise HTTPException(
            status_code=429,
            detail=f"Çok fazla hatalı deneme yapıldı. Lütfen {remaining} saniye sonra tekrar deneyin.",
        )

    if payload is not None:
        password = payload.password
    else:
        try:
            data = await request.json()
            password = data.get("password", "") if isinstance(data, dict) else ""
        except Exception:
            password = ""

    if configured_pwd and not secrets.compare_digest(
        str(password or "").encode("utf-8"),
        str(configured_pwd).encode("utf-8"),
    ):
        auth_mod._register_login_failure(client_host, now)
        raise HTTPException(status_code=401, detail="Hatalı şifre.")

    auth_mod._clear_login_attempts(client_host)

    auth_mod._set_session_authenticated(request, True)
    return auth_mod._auth_success_response()


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    """Logout endpoint."""
    auth_mod._ensure_safe_request_origin(request)
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token:
        with auth_mod._auth_lock:
            auth_mod.AUTH_STATE["valid_tokens"].pop(token, None)
    try:
        request.session.clear()
    except Exception as e:
        import logging

        logging.debug("Session clear error during logout: %s", e)
    resp = JSONResponse({"status": "logged_out"})
    resp.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return resp


@router.post(
    "/invalidate-all",
    responses={403: {"description": "Yetkisiz erişim"}},
)
async def auth_invalidate_all(request: Request) -> JSONResponse:
    """Invalidate all remote sessions."""
    auth_mod._ensure_authorized(request)
    auth_mod._rotate_auth_boot_id()
    resp = JSONResponse({"status": "ok", "message": "Tüm uzak oturumlar geçersiz kılındı."})
    resp.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return resp


@router.post(
    "/handoff-token",
    responses={
        400: {"description": "file_hash is required"},
        403: {"description": "Yetkisiz erişim"},
    },
)
async def generate_handoff_token(request: Request) -> dict:
    """Generate temporary handoff token and LAN QR code for seamless mobile reading."""
    auth_mod._ensure_authorized(request)
    try:
        data = await request.json()
    except Exception:
        data = {}
    file_hash = str(data.get("file_hash") or "").strip()
    page_number = int(data.get("page_number") or 1)
    if not file_hash:
        raise HTTPException(status_code=400, detail="file_hash is required")

    from app.services.handoff_service import (
        create_handoff_token,
        generate_qr_svg,
        get_local_lan_ip,
    )

    token = create_handoff_token(file_hash, page_number)
    lan_ip = get_local_lan_ip()

    # Resolve correct scheme: detect HTTP vs HTTPS (handles reverse proxies via X-Forwarded-Proto)
    scheme = request.url.scheme or "http"
    if request.headers.get("x-forwarded-proto"):
        scheme = request.headers.get("x-forwarded-proto").split(",")[0].strip()

    port = request.url.port
    if (scheme == "http" and (port == 80 or not port)) or (
        scheme == "https" and (port == 443 or not port)
    ):
        port_str = ""
    else:
        port_str = f":{port or 8000}"

    handoff_url = f"{scheme}://{lan_ip}{port_str}/handoff/{token}"
    qr_svg = generate_qr_svg(handoff_url)

    return {
        "token": token,
        "url": handoff_url,
        "qr_svg": qr_svg,
        "lan_ip": lan_ip,
        "expires_in_seconds": 86400 * 30,
    }
