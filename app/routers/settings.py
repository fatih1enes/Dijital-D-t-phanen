"""Settings and logging endpoints router."""

import asyncio
import json
import os
import tempfile
import time
import zipfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from app.auth import _ensure_authorized
from app.config import CONFIG_DEFAULTS, load_config, save_config
from app.logger import clear_log_buffer, get_logs_snapshot, log_event
from app.models import SettingsUpdateRequest

router = APIRouter(prefix="/api", tags=["settings"])

MASKED_KEY = "••••••••"
CONF_ACCESS_PASSWORD = "access_password"
CONF_AI_API_KEY = "ai_api_key"
CONF_TELEGRAM_HASH = "telegram_api_hash"


def _get_cfg_handlers() -> tuple:
    return load_config, save_config


def _get_local_ip() -> str:
    """Detect LAN IPv4 address for mobile/remote access display."""
    import socket

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe_ip = os.environ.get("ROUTING_PROBE_IP", "10.255.255.255")  # NOSONAR
        s.connect((probe_ip, 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _sync_password_to_env(new_pwd: str) -> None:
    """Sync ACCESS_PASSWORD to .env file."""
    from app.constants import PROJECT_ROOT

    env_path = os.path.join(PROJECT_ROOT, ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                lines = f.readlines()
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith("ACCESS_PASSWORD="):
                new_lines.append(f"ACCESS_PASSWORD={new_pwd}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"\nACCESS_PASSWORD={new_pwd}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        try:
            os.chmod(env_path, 0o600)
        except OSError as e:
            log_event(
                "config",
                "DEBUG",
                f"Platform does not support chmod 0600 on {env_path}: {e}",
            )
    except Exception as e:
        log_event("config", "DEBUG", f"Could not sync password to .env: {e}")


def _filter_secret_keys(filtered: dict) -> None:
    """Preserve existing secret keys if masked or left blank."""
    for secret_key in (CONF_AI_API_KEY, CONF_TELEGRAM_HASH):
        if secret_key in filtered:
            val = str(filtered[secret_key] or "").strip()
            if not val or val.startswith("••") or val == MASKED_KEY or "•" in val:
                filtered.pop(secret_key, None)


def _process_access_password_update(filtered: dict) -> None:
    """Handle access_password update or removal."""
    if CONF_ACCESS_PASSWORD not in filtered:
        return
    raw_pwd = str(filtered[CONF_ACCESS_PASSWORD] or "").strip()
    import app.auth as auth_mod

    if raw_pwd == "__REMOVE__":
        filtered[CONF_ACCESS_PASSWORD] = ""
        os.environ["ACCESS_PASSWORD"] = ""
        auth_mod.ACCESS_PASSWORD = ""
        _sync_password_to_env("")
    elif raw_pwd and not raw_pwd.startswith("••") and raw_pwd != MASKED_KEY:
        filtered[CONF_ACCESS_PASSWORD] = raw_pwd
        os.environ["ACCESS_PASSWORD"] = raw_pwd
        auth_mod.ACCESS_PASSWORD = raw_pwd
        _sync_password_to_env(raw_pwd)
    else:
        filtered.pop(CONF_ACCESS_PASSWORD, None)


@router.get("/settings")
async def api_get_settings(request: Request) -> dict:
    """Get settings (excluding sensitive keys)."""
    _ensure_authorized(request)

    load_cfg, _ = _get_cfg_handlers()
    cfg = load_cfg()

    # Check if keys are present in environment or config for UI feedback
    cfg["has_gemini_key"] = bool(os.environ.get("GEMINI_API_KEY") or cfg.get(CONF_AI_API_KEY))
    cfg["has_ai_api_key"] = bool(cfg.get(CONF_AI_API_KEY) or os.environ.get("GEMINI_API_KEY"))
    cfg["has_telegram_hash"] = bool(cfg.get(CONF_TELEGRAM_HASH))

    from app.auth import _get_access_password

    active_pwd = _get_access_password()
    cfg["has_access_password"] = bool(active_pwd)
    cfg[CONF_ACCESS_PASSWORD] = MASKED_KEY if active_pwd else ""
    local_ip = _get_local_ip()
    cfg["local_ip"] = local_ip
    scheme = (
        "https"
        if request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
        else "http"
    )
    port = request.url.port or 8000
    cfg["phone_url"] = f"{scheme}://{local_ip}:{port}"

    # Mask sensitive API keys to prevent plain text exfiltration
    cfg[CONF_AI_API_KEY] = MASKED_KEY if cfg.get(CONF_AI_API_KEY) else ""
    cfg[CONF_TELEGRAM_HASH] = MASKED_KEY if cfg.get(CONF_TELEGRAM_HASH) else ""

    return cfg


@router.post(
    "/settings",
    responses={400: {"description": "Invalid settings data"}},
)
async def update_settings(request: Request, payload: SettingsUpdateRequest | None = None) -> dict:
    """Update settings."""
    _ensure_authorized(request)

    if payload is not None:
        settings = payload.model_dump(exclude_unset=True)
    else:
        raw = await request.json()
        if not isinstance(raw, dict):
            raise HTTPException(status_code=400, detail="Invalid settings data")
        settings = raw

    load_cfg, save_cfg = _get_cfg_handlers()
    current = load_cfg()
    allowed = set(CONFIG_DEFAULTS.keys())
    filtered = {key: value for key, value in settings.items() if key in allowed}

    _filter_secret_keys(filtered)
    _process_access_password_update(filtered)

    current.update(filtered)
    save_cfg(current)

    if "gemini_cascade_models" in filtered:
        cascade_models = current.get("gemini_cascade_models") or []
        try:
            from app.services.cascade_manager import cascade_manager

            cascade_manager.configure_chain(cascade_models)
        except Exception as e:
            log_event(
                "settings",
                "DEBUG",
                f"Failed to configure cascade chain: {e}",
                error=str(e),
            )

    return {"status": "saved"}


@router.get("/settings/watchfolder")
async def get_watchfolder_status(request: Request) -> dict:
    """Get status of the background auto-watchfolder service."""
    _ensure_authorized(request)
    from app.services.watchfolder_service import watchfolder_service

    return watchfolder_service.get_status()


@router.post("/settings/watchfolder/scan")
async def trigger_watchfolder_scan(request: Request) -> dict:
    """Manually trigger an immediate scan of the configured watchfolder."""
    _ensure_authorized(request)
    from app.services.watchfolder_service import watchfolder_service

    load_cfg, _ = _get_cfg_handlers()
    cfg = load_cfg()
    watch_dir = str(cfg.get("watchfolder_path", "")).strip()
    if not watch_dir or not os.path.exists(watch_dir):
        return {
            "status": "error",
            "message": "Watchfolder directory does not exist or is not configured",
            "enqueued": 0,
        }
    count = await watchfolder_service.scan_directory(watch_dir)
    return {"status": "success", "enqueued": count}


@router.post(
    "/database/backup",
    responses={500: {"description": "Backup failed"}},
)
async def backup_database_endpoint(request: Request) -> dict:
    """Trigger a consistent point-in-time snapshot backup of the library database."""
    _ensure_authorized(request)
    from app.database import create_database_backup

    try:
        backup_path = await create_database_backup()
        return {"status": "success", "backup_path": backup_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {e}") from e


def _add_library_files_to_zip(zf: zipfile.ZipFile, library_root: str) -> None:
    """Walk and write library documents into archive."""
    if not os.path.exists(library_root):
        return
    parent_dir = os.path.dirname(library_root)
    for root, _, files in os.walk(library_root):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, parent_dir)
            zf.write(file_path, arcname=rel_path)


def _add_db_and_config_to_zip(zf: zipfile.ZipFile, backup_db_path: str, config_file: str) -> None:
    """Add database backup and config to archive."""
    if os.path.exists(backup_db_path):
        zf.write(backup_db_path, arcname="kutuphane.db")
        try:
            os.remove(backup_db_path)
        except OSError as rm_err:
            log_event("system", "DEBUG", f"Backup db cleanup notice: {rm_err}")
    if os.path.exists(config_file):
        zf.write(config_file, arcname="config.json")


@router.get("/database/export-full-zip")
async def export_full_library_zip(request: Request) -> FileResponse:
    """Creates a complete portable ZIP containing database, configuration, and library documents."""
    _ensure_authorized(request)
    import app.config as app_config
    from app.constants import LIBRARY_ROOT
    from app.database import create_database_backup

    backup_db_path = await create_database_backup()

    tmp_fd, tmp_zip_path = tempfile.mkstemp(prefix="Dijital_Kutuphane_Yedek_", suffix=".zip")
    os.close(tmp_fd)

    def _build_zip() -> None:
        with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            _add_db_and_config_to_zip(zf, backup_db_path, app_config.CONFIG_PATH)
            _add_library_files_to_zip(zf, LIBRARY_ROOT)

            manifest = {
                "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0.0",
                "system": "Dijital Kütüphane Taşınabilir Yedek Paketi",
            }
            zf.writestr("yedek_bilgisi.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    try:
        await asyncio.to_thread(_build_zip)
    except Exception:
        for leftover in (tmp_zip_path, backup_db_path):
            if leftover and os.path.exists(leftover):
                try:
                    os.remove(leftover)
                except OSError as rm_err:
                    log_event("system", "DEBUG", f"Zip error cleanup notice: {rm_err}")
        raise

    def _cleanup() -> None:
        try:
            if os.path.exists(tmp_zip_path):
                os.remove(tmp_zip_path)
        except OSError as cleanup_err:
            log_event("system", "DEBUG", f"Temp zip cleanup notice: {cleanup_err}")

    date_str = time.strftime("%Y%m%d_%H%M")
    filename = f"Dijital_Kutuphane_Tam_Yedek_{date_str}.zip"
    return FileResponse(
        tmp_zip_path,
        media_type="application/zip",
        filename=filename,
        background=BackgroundTask(_cleanup),
    )


@router.get("/logs")
async def get_logs(
    request: Request,
    category: str | None = None,
    level: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> dict:
    """Get application logs with optional category, level, and text query filtering."""
    _ensure_authorized(request)
    return get_logs_snapshot(category=category, level=level, query=q, limit=limit)


@router.post("/logs/clear")
async def clear_logs_endpoint(request: Request) -> dict:
    """Clear in-memory logs."""
    _ensure_authorized(request)
    cleared = clear_log_buffer()
    return {"status": "success", "cleared": cleared}


@router.get("/logs/export")
async def export_logs_endpoint(request: Request, format: str = "json") -> Response:
    """Export in-memory logs as a downloadable file (JSON or formatted text log)."""
    _ensure_authorized(request)
    snapshot = get_logs_snapshot(limit=2000)
    logs_data = snapshot["logs"]
    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format.lower() in ("log", "txt"):
        lines = []
        for log_item in logs_data:
            iso = log_item.get("iso") or datetime.fromtimestamp(log_item.get("ts", 0)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            lvl = log_item.get("level", "INFO")
            cat = log_item.get("category", "system")
            msg = log_item.get("message", "")
            ctx = log_item.get("context", {})
            lines.append(f"[{iso}] [{lvl:<5}] [{cat}] {msg} | {ctx}")
        content = "\n".join(lines)
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="kutuphane_logs_{ts_str}.log"'},
        )

    json_bytes = json.dumps(logs_data, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="kutuphane_logs_{ts_str}.json"'},
    )
