"""Task status endpoints router."""

from fastapi import APIRouter, HTTPException, Request

from app.auth import _ensure_authorized
from app.tasks import _tasks_lock, active_tasks, archived_tasks, prune_tasks

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def get_active_tasks(request: Request) -> dict:
    """Get all active and archived tasks with cleanup."""
    _ensure_authorized(request)
    prune_tasks()
    with _tasks_lock:
        return {"active": dict(active_tasks), "archived": dict(archived_tasks)}


@router.get("/{task_id}", responses={404: {"description": "Task not found"}})
async def get_task_status(task_id: str, request: Request) -> dict:
    """Get individual task status."""
    _ensure_authorized(request)
    with _tasks_lock:
        task = active_tasks.get(task_id) or archived_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(task)
