from collections.abc import AsyncGenerator
from typing import Any

from app.database import DatabaseManager, get_db_context


async def get_db() -> AsyncGenerator[DatabaseManager, None]:
    """FastAPI Dependency Injection yielding a DatabaseManager instance per request."""
    async with get_db_context() as db:
        yield db


def get_task_queue() -> Any:
    """Retrieve the global TaskQueue instance from FastAPI app state."""
    import app.main

    return getattr(app.main.app.state, "task_queue", None)
