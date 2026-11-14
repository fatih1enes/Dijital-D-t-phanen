"""Telegram authentication and synchronization endpoints router."""

import asyncio

from fastapi import APIRouter, Header, HTTPException, Request

from app.auth import _ensure_authorized
from app.config import load_config
from app.models import (
    TelegramSendCodeRequest,
    TelegramSettingsRequest,
    TelegramSyncRequest,
    TelegramVerifyRequest,
)
from app.services.telegram_service import telegram_service

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.get("/status")
async def telegram_status(request: Request) -> dict:
    """Check Telegram connection status and account details."""
    _ensure_authorized(request)
    return await telegram_service.check_status()


@router.post("/channel")
async def telegram_update_channel(request: Request, payload: TelegramSettingsRequest) -> dict:
    """Update target Telegram chat or channel."""
    _ensure_authorized(request)
    return await telegram_service.save_chat_target(payload.chat_target)


@router.post("/auth/send-code", responses={400: {"description": "Kod gönderilemedi"}})
async def telegram_send_code(request: Request, payload: TelegramSendCodeRequest) -> dict:
    """Request SMS or in-app confirmation code from Telegram."""
    _ensure_authorized(request)

    res = await telegram_service.request_code(
        api_id=payload.api_id,
        api_hash=payload.api_hash,
        phone=payload.phone_number,
        chat_target=payload.chat_target,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Kod gönderilemedi."))
    return res


@router.post("/auth/verify", responses={400: {"description": "Doğrulama başarısız"}})
async def telegram_verify(request: Request, payload: TelegramVerifyRequest) -> dict:
    """Verify code (and optional 2FA cloud password) to establish session."""
    _ensure_authorized(request)

    res = await telegram_service.verify_code(
        code=payload.code,
        password=payload.password,
    )
    if not res.get("success"):
        if res.get("needs_password"):
            return {
                "success": False,
                "needs_password": True,
                "error": res.get("error", "2FA şifresi gerekli."),
            }
        raise HTTPException(status_code=400, detail=res.get("error", "Doğrulama başarısız."))
    return res


@router.post("/sync")
async def telegram_sync(
    request: Request,
    payload: TelegramSyncRequest | None = None,
    x_ai_key: str | None = Header(None, alias="X-AI-Key"),
    x_ai_provider: str | None = Header(None, alias="X-AI-Provider"),
    x_ai_model: str | None = Header(None, alias="X-AI-Model"),
    x_ai_model_name: str | None = Header(None, alias="X-AI-Model-Name"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-Url"),
) -> dict:
    """Start asynchronous Telegram document synchronization in the background."""
    _ensure_authorized(request)

    if telegram_service._is_syncing:
        return {
            "status": "already_running",
            "message": "Telegram senkronizasyonu şu anda zaten devam ediyor.",
        }

    from app.config import is_real_api_key, resolve_ai_credentials

    cfg = load_config()
    chat_target = payload.chat_target if payload else None
    key_candidate = (payload.api_key if payload else None) or x_ai_key
    prov_candidate = (payload.provider if payload else None) or x_ai_provider
    model_candidate = (payload.model_name if payload else None) or x_ai_model_name or x_ai_model
    url_candidate = (payload.base_url if payload else None) or x_ai_base_url

    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=prov_candidate,
        api_key=key_candidate,
        model=model_candidate,
        base_url=url_candidate,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    # Transient API key is kept in memory for the sync task rather than mutating config.json
    # Schedule sync as an asyncio task on the running loop
    task_queue = getattr(request.app.state, "task_queue", None)
    if not task_queue:
        from app.task_queue import TaskQueue

        task_queue = TaskQueue()
        request.app.state.task_queue = task_queue

    reset_cursor = bool(payload.reset_cursor) if payload else False

    sync_task = asyncio.create_task(
        telegram_service.sync_documents(
            task_queue=task_queue,
            chat_target=chat_target,
            api_key=api_key,
            provider=provider,
            model_name=model_name,
            base_url=base_url,
            reset_cursor=reset_cursor,
        )
    )
    bg_tasks = getattr(request.app.state, "background_tasks", None)
    if bg_tasks is not None:
        bg_tasks.add(sync_task)
        sync_task.add_done_callback(bg_tasks.discard)

    return {
        "status": "started",
        "message": "Telegram senkronizasyonu arka planda başlatıldı. İlerlemeyi canlı izleyebilirsiniz.",
    }


@router.post("/disconnect")
async def telegram_disconnect(request: Request) -> dict:
    """Disconnect active Telegram session and remove session data."""
    _ensure_authorized(request)

    return await telegram_service.disconnect()
