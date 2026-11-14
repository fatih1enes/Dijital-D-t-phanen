"""Configuration management for Dijital Kütüphane."""

import json
import os
import threading
import time
from typing import Any

from app.constants import DEFAULT_GEMINI_MODEL, PROJECT_ROOT

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
DEFAULT_CASCADE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

CONFIG_DEFAULTS = {
    "max_pages": 20,
    "ocr_pages": 20,
    "vision_pages": 20,
    "vision_max_image_dim": 1200,
    "vision_jpeg_quality": 82,
    "tesseract_cmd": "",
    "ai_provider": "gemini",
    "ai_api_key": "",
    "ai_base_url": "",
    "gemini_model": DEFAULT_GEMINI_MODEL,
    "ollama_model": "",
    "lmstudio_model": "",
    "ai_max_chars": 50000,
    "google_search_grounding": False,
    "gemini_cascade_mode": True,
    "gemini_cascade_models": list(DEFAULT_CASCADE_MODELS),
    "telegram_api_id": "",
    "telegram_api_hash": "",
    "telegram_chat_id": "me",
    "telegram_last_sync": "",
    "telegram_last_msg_id": 0,
    "access_password": "",
    "watchfolder_enabled": False,
    "watchfolder_path": "",
    "watchfolder_interval": 5,
}
CONFIG_NUMERIC_LIMITS = {
    "max_pages": (1, 100),
    "ocr_pages": (0, 60),
    "vision_pages": (0, 60),
    "vision_max_image_dim": (256, 2400),
    "vision_jpeg_quality": (40, 95),
    "ai_max_chars": (1000, 250000),
}


def _clean_cascade_models(raw_models: Any) -> list[str]:
    """Validate and clean list of cascade model names."""
    if isinstance(raw_models, list):
        clean_models = [str(m).strip() for m in raw_models if str(m).strip()]
        if clean_models:
            return clean_models
    return list(DEFAULT_CASCADE_MODELS)


def _apply_numeric_limits(data: dict, config: dict) -> None:
    """Enforce min and max limits for numeric configuration settings."""
    for key, (min_value, max_value) in CONFIG_NUMERIC_LIMITS.items():
        default_value = CONFIG_DEFAULTS[key]
        try:
            numeric_value = int(data.get(key, default_value))
        except (TypeError, ValueError):
            numeric_value = default_value
        config[key] = max(min_value, min(max_value, numeric_value))


def _extract_ai_config(data: dict) -> dict:
    """Extract and normalize AI-related settings."""
    return {
        "ai_provider": str(data.get("ai_provider", CONFIG_DEFAULTS["ai_provider"]) or "").strip()
        or CONFIG_DEFAULTS["ai_provider"],
        "ai_api_key": str(data.get("ai_api_key", CONFIG_DEFAULTS["ai_api_key"]) or "").strip(),
        "ai_base_url": str(data.get("ai_base_url", CONFIG_DEFAULTS["ai_base_url"]) or "").strip(),
        "gemini_model": str(data.get("gemini_model", CONFIG_DEFAULTS["gemini_model"]) or "").strip()
        or CONFIG_DEFAULTS["gemini_model"],
        "ollama_model": str(
            data.get("ollama_model", CONFIG_DEFAULTS["ollama_model"]) or ""
        ).strip(),
        "lmstudio_model": str(
            data.get("lmstudio_model", CONFIG_DEFAULTS["lmstudio_model"]) or ""
        ).strip(),
        "google_search_grounding": bool(data.get("google_search_grounding", False)),
        "gemini_cascade_mode": bool(
            data.get("gemini_cascade_mode", CONFIG_DEFAULTS["gemini_cascade_mode"])
        ),
        "gemini_cascade_models": _clean_cascade_models(data.get("gemini_cascade_models")),
    }


def _extract_telegram_config(data: dict) -> dict:
    """Extract and normalize Telegram integration settings."""
    return {
        "telegram_api_id": str(
            data.get("telegram_api_id", CONFIG_DEFAULTS["telegram_api_id"]) or ""
        ).strip(),
        "telegram_api_hash": str(
            data.get("telegram_api_hash", CONFIG_DEFAULTS["telegram_api_hash"]) or ""
        ).strip(),
        "telegram_chat_id": str(
            data.get("telegram_chat_id", CONFIG_DEFAULTS["telegram_chat_id"]) or "me"
        ).strip(),
        "telegram_last_sync": str(
            data.get("telegram_last_sync", CONFIG_DEFAULTS["telegram_last_sync"]) or ""
        ).strip(),
        "telegram_last_msg_id": int(data.get("telegram_last_msg_id", 0) or 0),
    }


def _normalize_config(raw_config: dict | None) -> dict:
    """Normalize configuration values."""
    data = raw_config if isinstance(raw_config, dict) else {}

    config = {
        "tesseract_cmd": str(
            data.get("tesseract_cmd", CONFIG_DEFAULTS["tesseract_cmd"]) or ""
        ).strip(),
        **_extract_ai_config(data),
        **_extract_telegram_config(data),
        "access_password": str(
            data.get("access_password", CONFIG_DEFAULTS.get("access_password", "")) or ""
        ).strip(),
        "watchfolder_enabled": bool(data.get("watchfolder_enabled", False)),
        "watchfolder_path": str(data.get("watchfolder_path", "") or "").strip(),
        "watchfolder_interval": max(2, min(300, int(data.get("watchfolder_interval", 5) or 5))),
    }
    _apply_numeric_limits(data, config)
    return config


_config_lock = threading.Lock()
_cached_config: dict | None = None
_cached_config_mtime: float = 0.0


def load_config() -> dict:
    """Load configuration with mtime-based in-memory caching to eliminate redundant disk I/O."""
    global _cached_config, _cached_config_mtime
    with _config_lock:
        try:
            current_mtime = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0.0
        except OSError:
            current_mtime = 0.0

        if _cached_config is not None and _cached_config_mtime == current_mtime:
            return dict(_cached_config)

        defaults = dict(CONFIG_DEFAULTS)
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, encoding="utf-8-sig") as f:
                    defaults.update(_normalize_config(json.load(f)))
            except (json.JSONDecodeError, OSError) as e:
                try:
                    from app.logger import log_event

                    log_event("config", "WARNING", f"Could not read config.json: {e}")
                except Exception as log_err:
                    import logging

                    logging.debug("Could not log config read warning: %s", log_err)

        normalized = _normalize_config(defaults)
        _cached_config = normalized
        _cached_config_mtime = current_mtime
        return dict(normalized)


def save_config(config: dict) -> None:
    """Save configuration to file and invalidate/update cache atomically with Windows retry."""
    global _cached_config, _cached_config_mtime
    normalized = _normalize_config(config)
    tmp_path = f"{CONFIG_PATH}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=4, ensure_ascii=False)

    with _config_lock:
        replaced = False
        for attempt in range(5):
            try:
                os.replace(tmp_path, CONFIG_PATH)
                replaced = True
                break
            except OSError:
                time.sleep(0.05 * (attempt + 1))

        if not replaced:
            os.replace(tmp_path, CONFIG_PATH)

        try:
            _cached_config_mtime = os.path.getmtime(CONFIG_PATH)
        except OSError:
            _cached_config_mtime = 0.0
        _cached_config = normalized


def configure_tesseract_from_config(config: dict) -> str:
    """Configure Tesseract OCR command from config if specified, with Windows auto-detection."""
    import os

    import pytesseract

    tess_cmd = str(config.get("tesseract_cmd") or "").strip()

    # Windows auto-detection if not explicitly set
    if not tess_cmd and os.name == "nt":
        default_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_cmd):
            tess_cmd = default_cmd

    if tess_cmd and os.path.isfile(tess_cmd):
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
        return tess_cmd
    return ""


def is_real_api_key(key: str | None) -> bool:
    """Check if an API key is a genuine key and not a masked UI placeholder (e.g. ••••••••)."""
    if not key:
        return False
    s = str(key).strip()
    if not s or s.startswith("••") or "•" in s or s == "••••••••":
        return False
    return True


def _resolve_candidate_api_key(api_key: str | None, cfg: dict, is_key_fn: Any) -> str:
    """Resolve active API key across parameter, config, and environment candidates."""
    candidates = [
        str(api_key or "").strip(),
        str(cfg.get("ai_api_key") or "").strip(),
        str(os.environ.get("GEMINI_API_KEY") or "").strip(),
    ]
    for cand in candidates:
        if cand and is_key_fn(cand):
            return cand
    return ""


def resolve_ai_credentials(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    cfg: dict | None = None,
    is_key_fn: Any = None,
) -> tuple[str, str, str, str]:
    """Unified resolution of AI credentials across headers, config, and environment.

    Returns:
        tuple[str, str, str, str]: (provider, api_key, model_name, base_url)
    """
    if cfg is None:
        cfg = load_config()
    if is_key_fn is None:
        is_key_fn = is_real_api_key

    prov = str(provider or cfg.get("ai_provider") or "gemini").strip().lower()
    resolved_key = _resolve_candidate_api_key(api_key, cfg, is_key_fn)

    resolved_model = model or cfg.get(f"{prov}_model")
    if not resolved_model and prov == "gemini":
        from app.constants import DEFAULT_GEMINI_MODEL

        resolved_model = DEFAULT_GEMINI_MODEL

    resolved_base_url = str(base_url or cfg.get("ai_base_url") or "").strip()

    return prov, resolved_key, str(resolved_model or ""), resolved_base_url
