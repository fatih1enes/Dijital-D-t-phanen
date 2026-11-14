"""Logging functions for Dijital Kütüphane."""

import asyncio
import logging
import os
import threading
import time
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any

from app.constants import DATA_DIR, MAX_LOGS
from app.utils import mask_sensitive_data

# Log directory and file setup
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")

# Setup RotatingFileHandler (5 MB per file, up to 5 backups)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
rotating_file_handler = RotatingFileHandler(
    LOG_FILE_PATH,
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
rotating_file_handler.setFormatter(file_formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(file_formatter)

# Configure Root Logger
_raw_log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
DEFAULT_LOG_LEVEL = getattr(logging, _raw_log_level, logging.INFO)

root_logger = logging.getLogger()
root_logger.setLevel(DEFAULT_LOG_LEVEL)
# Avoid duplicate handlers if reloaded
if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
    root_logger.addHandler(rotating_file_handler)
if not any(
    isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
    for h in root_logger.handlers
):
    root_logger.addHandler(stream_handler)

# Thread-safe ring buffer for in-memory log history
_buffer_lock = threading.Lock()
LOG_BUFFER = deque(maxlen=MAX_LOGS)

_counter_lock = threading.Lock()
_log_seq_counter = 0

GLOBAL_LOOP = None
ws_manager = None

# Category aliases to normalize logging across subsystems
CATEGORY_NORMALIZE = {
    "pdf_processing": "pdf",
    "ocr": "pdf",
    "task": "upload",
    "watchfolder": "upload",
    "telegram": "upload",
    "document": "pdf",
    "cascade": "ai_analyze",
    "database": "system",
    "config": "system",
    "websocket": "system",
}

LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "SUCCESS": logging.INFO,
    "PROCESSING": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.CRITICAL,
}


def _normalize_level(lvl: str | None) -> str:
    """Normalize any arbitrary level string to standard UI level (DEBUG, INFO, WARNING, ERROR)."""
    clean = str(lvl or "INFO").strip().upper()
    if clean in ("ERROR", "CRITICAL", "FATAL"):
        return "ERROR"
    if clean in ("WARNING", "WARN"):
        return "WARNING"
    if clean == "DEBUG":
        return "DEBUG"
    return "INFO"


def _next_log_id() -> str:
    """Generate a unique monotonically increasing log ID."""
    global _log_seq_counter
    with _counter_lock:
        _log_seq_counter += 1
        return f"log_{int(time.time() * 1000)}_{_log_seq_counter}"


def normalize_category(category: str | None) -> str:
    """Normalize category strings into standardized frontend categories."""
    if not category:
        return "system"
    clean = str(category).strip().lower()
    return CATEGORY_NORMALIZE.get(clean, clean)


def set_ws_manager(manager: Any) -> None:
    """Set WebSocket manager for logging."""
    global ws_manager
    ws_manager = manager


def set_global_loop(loop: Any) -> None:
    """Set global event loop."""
    global GLOBAL_LOOP
    GLOBAL_LOOP = loop


def notify_ws(msg_type: str, data: dict) -> None:
    """Send notification via WebSocket safely from any thread or async context."""
    if ws_manager is None:
        return
    msg = {"type": msg_type, "data": data, "payload": data, "timestamp": time.time()}

    # Check if we are currently running inside the global event loop thread
    try:
        current_loop = asyncio.get_running_loop()
        if not current_loop.is_closed():
            current_loop.create_task(ws_manager.broadcast(msg))
            return
    except RuntimeError:
        logging.debug("No running loop in current thread, using GLOBAL_LOOP")

    # Called from a worker/background thread: schedule safely onto GLOBAL_LOOP
    if GLOBAL_LOOP is not None and not GLOBAL_LOOP.is_closed() and GLOBAL_LOOP.is_running():
        try:
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast(msg), GLOBAL_LOOP)
        except Exception as e:
            logging.debug("Could not schedule coroutine to GLOBAL_LOOP: %s", e)


def _append_to_buffer(
    category: str, level: str, message: str, context: dict, origin: str = "app"
) -> dict:
    """Internal helper to atomically append a log entry to the ring buffer with sensitive data masked."""
    std_level = _normalize_level(level)
    now = time.time()
    iso_time = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")

    clean_message = mask_sensitive_data(str(message))
    clean_context = {
        k: (mask_sensitive_data(str(v)) if isinstance(v, (str, Exception)) else v)
        for k, v in (context or {}).items()
    }

    entry = {
        "id": _next_log_id(),
        "ts": now,
        "iso": iso_time,
        "category": normalize_category(category),
        "raw_category": category,
        "level": std_level,
        "message": clean_message,
        "context": clean_context,
        "origin": origin,
    }

    with _buffer_lock:
        LOG_BUFFER.append(entry)

    notify_ws("log", entry)
    return entry


def log_event(category: str, level: str, message: str, **context) -> dict:
    """Log an application event with structured context and broadcast to live listeners."""
    level = level.upper()
    entry = _append_to_buffer(
        category=category,
        level=level,
        message=message,
        context=context,
        origin="log_event",
    )

    py_level = LEVEL_MAP.get(level, logging.INFO)
    extra_data = {"_from_log_event": True, "category": category}
    logging.log(py_level, f"[{category}] {message} | {context}", extra=extra_data)

    return entry


def _matches_log_filter(
    entry: dict,
    cat_filter: str | None,
    lvl_filter: str | None,
    q_filter: str | None,
) -> bool:
    """Check if a log entry satisfies snapshot filter criteria."""
    if cat_filter and entry.get("category") != cat_filter:
        return False
    if lvl_filter and entry.get("level") != lvl_filter:
        return False
    if q_filter:
        msg = entry.get("message", "").lower()
        cat_name = entry.get("category", "").lower()
        lvl_name = entry.get("level", "").lower()
        ctx_str = str(entry.get("context", "")).lower()
        if (
            q_filter not in msg
            and q_filter not in ctx_str
            and q_filter not in cat_name
            and q_filter not in lvl_name
        ):
            return False
    return True


def _compute_log_counts(
    all_entries: list[dict],
) -> tuple[dict[str, int], dict[str, int]]:
    """Compute aggregate counts by category and severity level."""
    counts_by_cat: dict[str, int] = {}
    counts_by_level: dict[str, int] = {
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
        "CRITICAL": 0,
    }
    for e in all_entries:
        c = e.get("category", "system")
        counts_by_cat[c] = counts_by_cat.get(c, 0) + 1
        lvl = e.get("level", "INFO")
        counts_by_level[lvl] = counts_by_level.get(lvl, 0) + 1
    return counts_by_cat, counts_by_level


def get_logs_snapshot(
    category: str | None = None,
    level: str | None = None,
    query: str | None = None,
    limit: int = 200,
) -> dict:
    """Thread-safely snapshot, filter, and summarize logs from the ring buffer."""
    with _buffer_lock:
        all_entries = list(LOG_BUFFER)

    cat_filter = normalize_category(category) if category and category.lower() != "all" else None
    lvl_filter = level.upper() if level and level.upper() != "ALL" else None
    q_filter = query.strip().lower() if query and query.strip() else None

    counts_by_cat, counts_by_level = _compute_log_counts(all_entries)
    filtered = [
        entry
        for entry in all_entries
        if _matches_log_filter(entry, cat_filter, lvl_filter, q_filter)
    ]

    limit = max(1, min(limit, 2000))
    logs_slice = filtered[-limit:]

    return {
        "logs": logs_slice,
        "total": len(filtered),
        "buffer_size": len(all_entries),
        "available_categories": sorted(counts_by_cat.keys()),
        "counts": {
            "total": len(all_entries),
            "categories": counts_by_cat,
            "levels": counts_by_level,
        },
    }


def clear_log_buffer() -> int:
    """Clear all logs from the in-memory ring buffer and notify clients."""
    with _buffer_lock:
        cleared_count = len(LOG_BUFFER)
        LOG_BUFFER.clear()

    notify_ws("log_cleared", {"cleared_count": cleared_count})
    return cleared_count


class UnifiedLogBufferHandler(logging.Handler):
    """Log handler that captures standard Python logger records into the live buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        # Ignore events already emitted via log_event() to prevent duplicate captures
        if getattr(record, "_from_log_event", False):
            return

        name = record.name.lower()
        if "uvicorn" in name or "fastapi" in name or "starlette" in name:
            category = "system"
        elif "security" in name or "auth" in name:
            category = "security"
        elif "pdf" in name or "fitz" in name:
            category = "pdf"
        elif "ai" in name or "gemini" in name or "chroma" in name:
            category = "ai_analyze"
        else:
            category = "system"

        level = record.levelname.upper()
        msg = record.getMessage()

        context = {}
        if record.exc_info and record.exc_text:
            context["traceback"] = record.exc_text
        if hasattr(record, "filename") and record.filename:
            context["caller"] = f"{record.filename}:{record.lineno}"

        _append_to_buffer(
            category=category,
            level=level,
            message=msg,
            context=context,
            origin="python_logger",
        )


# Attach unified handler to capture all uncaught library and system logs
if not any(isinstance(h, UnifiedLogBufferHandler) for h in root_logger.handlers):
    unified_handler = UnifiedLogBufferHandler()
    unified_handler.setLevel(logging.INFO)
    root_logger.addHandler(unified_handler)
