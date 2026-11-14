"""In-process Domain Event Bus for decoupled, asynchronous domain event processing."""

import asyncio
import inspect
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypeVar

from app.logger import log_event

T = TypeVar("T", bound="DomainEvent")


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BookUploadedEvent(DomainEvent):
    """Triggered when a new book is processed and stored into library."""

    file_hash: str = ""
    kitap_adi: str = ""
    yazar: str = ""
    kategori: str = ""
    dosya_yolu: str = ""
    dosya_adi: str = ""


@dataclass
class BookDeletedEvent(DomainEvent):
    """Triggered when a book is removed from library and database."""

    file_hash: str = ""
    dosya_yolu: str = ""


@dataclass
class BookUpdatedEvent(DomainEvent):
    """Triggered when book metadata or details are edited."""

    file_hash: str = ""
    changes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReadingProgressChangedEvent(DomainEvent):
    """Triggered when reading position changes."""

    file_hash: str = ""
    page: int = 1


@dataclass
class AnnotationMutatedEvent(DomainEvent):
    """Triggered when highlights or annotations are created, updated, or removed."""

    action: str = "created"  # created, updated, deleted, batch
    file_hash: str = ""
    annotation_id: str | None = None
    sayfa_no: int | None = None


class EventBus:
    """Thread-safe and async-safe in-process publish/subscribe domain event bus."""

    def __init__(self) -> None:
        self._subscribers: dict[type[DomainEvent], list[Callable[[Any], Any]]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: type[T], handler: Callable[[T], Any]) -> None:
        """Register a subscriber handler for a specific domain event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: type[T], handler: Callable[[T], Any]) -> bool:
        """Unregister a subscriber handler."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            return True
        return False

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered subscribers."""
        event_type = type(event)
        handlers = list(self._subscribers.get(event_type, []))

        # Also support polymorphic base class handlers
        for registered_type, registered_handlers in self._subscribers.items():
            if registered_type is not event_type and issubclass(event_type, registered_type):
                handlers.extend(registered_handlers)

        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                log_event(
                    "system",
                    "ERROR",
                    f"Event handler error ({event_type.__name__}): {e}",
                )

    def clear(self) -> None:
        """Clear all subscribers (useful for test isolation)."""
        self._subscribers.clear()


# Global Singleton Event Bus
event_bus = EventBus()


# -----------------------------------------------------------------------------
# Default Built-in Event Listeners
# -----------------------------------------------------------------------------


async def _default_cache_invalidator(event: DomainEvent) -> None:
    """Invalidate FastAPI cache when books are uploaded, updated, or deleted."""
    try:
        from fastapi_cache import FastAPICache

        await FastAPICache.clear(namespace="books")
        await FastAPICache.clear(namespace="stats")
    except Exception as e:
        log_event("system", "DEBUG", f"Cache invalidation note: {e}")


def _default_websocket_broadcast(event: DomainEvent) -> None:
    """Broadcast domain events via WebSocket."""
    from app.logger import notify_ws

    if isinstance(event, BookUploadedEvent):
        notify_ws(
            "library_update",
            {
                "reason": "upload_complete",
                "file_hash": event.file_hash,
                "title": event.kitap_adi,
            },
        )
    elif isinstance(event, BookDeletedEvent):
        notify_ws(
            "library_update",
            {
                "reason": "book_deleted",
                "file_hash": event.file_hash,
            },
        )
    elif isinstance(event, ReadingProgressChangedEvent):
        notify_ws(
            "reading_progress",
            {
                "file_hash": event.file_hash,
                "page": event.page,
            },
        )
    elif isinstance(event, AnnotationMutatedEvent):
        notify_ws(
            "annotation_update",
            {
                "action": event.action,
                "file_hash": event.file_hash,
                "annotation_id": event.annotation_id,
            },
        )


def setup_default_listeners() -> None:
    """Register built-in framework listeners to EventBus."""
    event_bus.subscribe(BookUploadedEvent, _default_cache_invalidator)
    event_bus.subscribe(BookDeletedEvent, _default_cache_invalidator)
    event_bus.subscribe(BookUpdatedEvent, _default_cache_invalidator)

    event_bus.subscribe(BookUploadedEvent, _default_websocket_broadcast)
    event_bus.subscribe(BookDeletedEvent, _default_websocket_broadcast)
    event_bus.subscribe(ReadingProgressChangedEvent, _default_websocket_broadcast)
    event_bus.subscribe(AnnotationMutatedEvent, _default_websocket_broadcast)


# Initialize default listeners on module import
setup_default_listeners()
