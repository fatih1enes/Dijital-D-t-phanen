"""Background task management."""

import threading
import time

_tasks_lock = threading.Lock()
active_tasks = {}
archived_tasks = {}
MAX_ACTIVE_TASKS = 200
MAX_ARCHIVED_TASKS = 50

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
FIELD_LAST_UPDATE = "last_update"
FIELD_ARCHIVED_AT = "archived_at"
FIELD_STATUS = "status"
FIELD_LOGS = "logs"


def _collect_stale_active_tasks(tasks: dict, now: float) -> list[str]:
    """Find active tasks eligible for archiving."""
    to_archive = []
    for tid, t in tasks.items():
        age = now - t.get(FIELD_LAST_UPDATE, now)
        if (t.get(FIELD_STATUS) in (STATUS_SUCCESS, STATUS_ERROR) and age > 15) or age > 120:
            to_archive.append(tid)
    return to_archive


def _archive_task_items(to_archive: list[str]) -> None:
    """Move active tasks to archived_tasks and keep under MAX_ARCHIVED_TASKS."""
    for tid in to_archive:
        item = active_tasks.pop(tid, None)
        if item:
            item[FIELD_ARCHIVED_AT] = time.time()
            archived_tasks[tid] = item
            if len(archived_tasks) > MAX_ARCHIVED_TASKS:
                oldest = sorted(
                    archived_tasks.items(),
                    key=lambda kv: kv[1].get(FIELD_ARCHIVED_AT, 0),
                )[:5]
                for oid, _ in oldest:
                    archived_tasks.pop(oid, None)


def _purge_expired_archived_tasks(now: float, ttl_seconds: float = 600.0) -> None:
    """Remove archives older than TTL."""
    old_arch = [
        tid
        for tid, t in archived_tasks.items()
        if now - t.get(FIELD_ARCHIVED_AT, now) > ttl_seconds
    ]
    for tid in old_arch:
        archived_tasks.pop(tid, None)


def _trim_active_tasks_if_overflow() -> None:
    """Evict oldest active tasks if hard capacity limit is exceeded."""
    if len(active_tasks) > MAX_ACTIVE_TASKS:
        oldest_active = sorted(
            active_tasks.items(), key=lambda kv: kv[1].get(FIELD_LAST_UPDATE, 0)
        )[:20]
        for o_tid, _ in oldest_active:
            active_tasks.pop(o_tid, None)


def prune_tasks(now: float | None = None) -> None:
    """Safely prune completed/stale tasks to keep memory bounded."""
    if now is None:
        now = time.time()
    with _tasks_lock:
        to_archive = _collect_stale_active_tasks(active_tasks, now)
        _archive_task_items(to_archive)
        _purge_expired_archived_tasks(now)
        _trim_active_tasks_if_overflow()


def update_task_status(
    task_id: str,
    status: str,
    percentage: int,
    message: str,
    log_state: str | None = None,
    task_data: dict | None = None,
) -> None:
    """Update status of a background task and notify clients via WebSocket."""
    from app.logger import notify_ws

    with _tasks_lock:
        task = active_tasks.get(task_id) or archived_tasks.get(task_id)
        if not task:
            return

        task.update(
            {
                "status": status,
                "percentage": percentage,
                "log_message": message,
                "last_update": time.time(),
            }
        )

        if task_data:
            task["task_data"] = task_data

        # Maintain logs list for frontend Operations Center
        logs = task.setdefault("logs", [])
        logs.append(
            {
                "ts": time.time(),
                "message": message,
                "status": status,
                "state": log_state or status,
                "pct": percentage,
            }
        )
        if len(logs) > 40:
            task["logs"] = logs[-40:]

        task_snapshot = dict(task)
        task_snapshot["logs"] = list(task.get("logs", []))

    # Periodic pruning on terminal status to bound memory
    if status in (STATUS_SUCCESS, STATUS_ERROR):
        prune_tasks()

    # Send WS update matching frontend format: type="task", data={task_id, task}
    notify_ws("task", {"task_id": task_id, "task": task_snapshot})

    # If a log_state is provided, also send a log event for the Log Center
    if log_state:
        from app.logger import log_event

        log_event("task", log_state.upper(), message, task_id=task_id)


class GeminiRateLimiter:
    """Rate limiter for Gemini API tracking both RPM (Requests) and TPM (Tokens)."""

    def __init__(self, rpm=13, tpm=210000):
        self.rpm = rpm
        self.tpm = tpm
        self.request_history = []  # list of (timestamp, token_count)
        self._lock = threading.Lock()

    @property
    def request_times(self) -> list[float]:
        """Backward compatibility for any code expecting request_times list."""
        with self._lock:
            return [t for t, _ in self.request_history]

    def wait_if_needed(self, estimated_tokens: int = 0, record: bool = True) -> None:
        """Wait if either RPM or TPM rate limit is reached in the sliding 60-second window."""
        while True:
            sleep_time = 0.0
            with self._lock:
                now = time.time()
                # Clean history older than 60 seconds
                self.request_history = [
                    (t, tok) for t, tok in self.request_history if now - t < 60.0
                ]

                needs_rpm = len(self.request_history) >= self.rpm
                current_tpm = sum(tok for _, tok in self.request_history)
                needs_tpm = (current_tpm + estimated_tokens) > self.tpm

                if (needs_rpm or needs_tpm) and self.request_history:
                    oldest_time = self.request_history[0][0]
                    sleep_time = max(0.5, 60.0 - (now - oldest_time) + 0.2)
                else:
                    if record:
                        self.request_history.append((now, max(1, estimated_tokens)))
                    break

            if sleep_time > 0:
                time.sleep(sleep_time)
