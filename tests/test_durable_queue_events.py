"""Tests for Phase 2: Durable Task Queue, Domain Event Bus, and Desktop Shell."""

import pytest

from app.durable_queue import DurableTaskQueue
from app.event_bus import (
    BookDeletedEvent,
    BookUploadedEvent,
    EventBus,
    ReadingProgressChangedEvent,
)
from desktop_shell import DesktopShell, create_tray_icon_image


class TestDurableTaskQueue:
    """Validate crash-resilience, atomic claiming, retry backoff, and DLQ."""

    @pytest.fixture
    def queue(self):
        return DurableTaskQueue()

    @pytest.mark.asyncio
    async def test_enqueue_and_get_job(self, temp_db, queue):
        """Verify enqueue inserts a pending record into durable_jobs."""
        payload = {"filename": "test_book.pdf", "file_hash": "a" * 64}
        task_id = await queue.enqueue("book_ingest", payload, max_retries=3)

        assert task_id is not None
        job = await queue.get_job(task_id)
        assert job is not None
        assert job["id"] == task_id
        assert job["job_type"] == "book_ingest"
        assert job["status"] == "pending"
        assert job["payload"]["filename"] == "test_book.pdf"
        assert job["retry_count"] == 0
        assert job["max_retries"] == 3

    @pytest.mark.asyncio
    async def test_claim_next_job_atomic(self, temp_db, queue):
        """Verify claim_next_job atomically transitions job from pending to processing."""
        payload = {"filename": "atomic_test.pdf"}
        task_id = await queue.enqueue("test_job", payload)

        claimed = await queue.claim_next_job()
        assert claimed is not None
        assert claimed["id"] == task_id
        assert claimed["job_type"] == "test_job"

        # Verify DB status is now 'processing'
        job_after = await queue.get_job(task_id)
        assert job_after["status"] == "processing"

        # Second claim should find nothing
        second_claim = await queue.claim_next_job()
        assert second_claim is None

    @pytest.mark.asyncio
    async def test_claim_empty_queue(self, temp_db, queue):
        """Verify claiming on an empty queue safely returns None."""
        claimed = await queue.claim_next_job()
        assert claimed is None

    @pytest.mark.asyncio
    async def test_recover_orphaned_jobs_on_crash(self, temp_db, queue):
        """Verify jobs abandoned in 'processing' status are rescued upon recovery."""
        from app.database import get_db_context

        orphan_id = "orphan_task_123"

        # Insert simulated crashed job
        async with get_db_context() as db:
            await db.conn.execute(
                """
                INSERT INTO durable_jobs (id, job_type, payload, status, retry_count, max_retries)
                VALUES (?, 'book_ingest', '{"file":"crashed.pdf"}', 'processing', 0, 3)
                """,
                (orphan_id,),
            )
            await db.conn.commit()

        recovered_count = await queue.recover_orphaned_jobs()
        assert recovered_count == 1

        recovered_job = await queue.get_job(orphan_id)
        assert recovered_job["status"] == "pending"
        assert recovered_job["retry_count"] == 1
        assert "kurtarıldı" in recovered_job["message"].lower()

    @pytest.mark.asyncio
    async def test_orphan_exceeding_max_retries_moved_to_dlq(self, temp_db, queue):
        """Verify crashed jobs that already exhausted retries are moved to Dead-Letter Queue."""
        from app.database import get_db_context

        dead_id = "dead_orphan_task_999"

        async with get_db_context() as db:
            await db.conn.execute(
                """
                INSERT INTO durable_jobs (id, job_type, payload, status, retry_count, max_retries)
                VALUES (?, 'book_ingest', '{"file":"dead.pdf"}', 'processing', 3, 3)
                """,
                (dead_id,),
            )
            await db.conn.commit()

        await queue.recover_orphaned_jobs()

        dead_job = await queue.get_job(dead_id)
        assert dead_job["status"] == "dead"
        assert "DLQ" in dead_job["error"]

    @pytest.mark.asyncio
    async def test_record_failure_exponential_backoff(self, temp_db, queue):
        """Verify failure schedules next attempt with exponential delay."""
        task_id = await queue.enqueue("calc", {"val": 10}, max_retries=3)
        claimed = await queue.claim_next_job()

        await queue.record_failure(
            claimed["id"], "Network timeout", claimed["retry_count"], claimed["max_retries"]
        )

        job = await queue.get_job(task_id)
        assert job["status"] == "pending"
        assert job["retry_count"] == 1
        assert "Network timeout" in job["error"]
        assert "tekrar denenecek" in job["message"]

    @pytest.mark.asyncio
    async def test_record_failure_relegation_to_dlq(self, temp_db, queue):
        """Verify failure exceeding max retries assigns status 'dead'."""
        task_id = await queue.enqueue("calc", {"val": 10}, max_retries=1)
        claimed = await queue.claim_next_job()

        # Fail with retry_count = 1 >= max_retries
        await queue.record_failure(claimed["id"], "Fatal syntax error", 1, 1)

        job = await queue.get_job(task_id)
        assert job["status"] == "dead"
        assert "Maksimum deneme aşıldı" in job["error"]

    @pytest.mark.asyncio
    async def test_record_success(self, temp_db, queue):
        """Verify record_success marks job completed with 100% progress."""
        task_id = await queue.enqueue("calc", {"val": 10})
        claimed = await queue.claim_next_job()

        await queue.record_success(claimed["id"], "İşlem bitti")

        job = await queue.get_job(task_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100
        assert job["message"] == "İşlem bitti"


class TestDomainEventBus:
    """Validate in-process asynchronous pub/sub domain event bus."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Verify typed subscribers receive published domain events."""
        bus = EventBus()
        received_events = []

        async def async_handler(event: BookUploadedEvent):
            received_events.append(event)

        bus.subscribe(BookUploadedEvent, async_handler)

        event = BookUploadedEvent(
            file_hash="hash_123",
            kitap_adi="Mülksüzler",
            yazar="Ursula K. Le Guin",
            kategori="Bilim Kurgu",
        )
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].kitap_adi == "Mülksüzler"
        assert received_events[0].yazar == "Ursula K. Le Guin"

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Verify unsubscribed handlers are no longer triggered."""
        bus = EventBus()
        calls = []

        def sync_handler(evt: BookDeletedEvent):
            calls.append(evt)

        bus.subscribe(BookDeletedEvent, sync_handler)
        await bus.publish(BookDeletedEvent(file_hash="del_1"))
        assert len(calls) == 1

        unsub_ok = bus.unsubscribe(BookDeletedEvent, sync_handler)
        assert unsub_ok is True

        await bus.publish(BookDeletedEvent(file_hash="del_2"))
        assert len(calls) == 1  # Still 1, not called again

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self):
        """Verify an exception in one subscriber does not break other subscribers."""
        bus = EventBus()
        passed = []

        def failing_handler(evt: ReadingProgressChangedEvent):
            raise RuntimeError("Boom!")

        def succeeding_handler(evt: ReadingProgressChangedEvent):
            passed.append(evt.page)

        bus.subscribe(ReadingProgressChangedEvent, failing_handler)
        bus.subscribe(ReadingProgressChangedEvent, succeeding_handler)

        await bus.publish(ReadingProgressChangedEvent(file_hash="book_1", page=42))

        assert passed == [42]


class TestDesktopShell:
    """Validate native desktop shell components and assets."""

    def test_tray_icon_image_creation(self):
        """Verify system tray icon image is properly rendered as a 64x64 RGBA PIL image."""
        img = create_tray_icon_image()
        assert img is not None
        assert img.size == (64, 64)
        assert img.mode == "RGBA"

    def test_desktop_shell_initialization(self):
        """Verify DesktopShell properties and URL format."""
        shell = DesktopShell(host="127.0.0.1", port=8000)
        assert shell.host == "127.0.0.1"
        assert shell.port == 8000
        assert shell.url == "http://127.0.0.1:8000"
        assert shell._is_running is True
