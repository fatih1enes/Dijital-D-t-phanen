"""Durable, crash-resilient SQLite-backed Task Queue with atomic claims and DLQ."""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any

from app.database import get_db_context
from app.logger import log_event, notify_ws
from app.tasks import update_task_status

logger = logging.getLogger(__name__)


class DurableTaskQueue:
    """Persistent task queue backed by SQLite `durable_jobs` table.

    Provides:
    - Atomic job claiming with SQLite 3.35+ `UPDATE ... RETURNING`
    - Crash recovery on boot (Orphan job rescue)
    - Exponential backoff with retry tracking
    - Dead-Letter Queue (DLQ) for poisoned tasks
    - Full threadpool offloading for CPU/IO heavy work
    """

    def __init__(self, max_workers: int = 1) -> None:
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="DurableWorker"
        )
        self._running = False
        self._wake_event = asyncio.Event()
        self._handlers: dict[str, Callable[[dict], Any]] = {}

    def register_handler(self, job_type: str, handler: Callable[[dict], Any]) -> None:
        """Register a handler callback for a specific job_type."""
        self._handlers[job_type] = handler

    async def enqueue(
        self,
        job_type: str,
        payload: dict[str, Any],
        task_id: str | None = None,
        max_retries: int = 3,
        delay_seconds: int = 0,
    ) -> str:
        """Enqueue a new persistent job into SQLite durable_jobs."""
        tid = task_id or str(uuid.uuid4())
        payload_json = json.dumps(payload, ensure_ascii=False)
        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        sched_str = scheduled_at.strftime("%Y-%m-%d %H:%M:%S")

        async with get_db_context() as db:
            query = """
                INSERT INTO durable_jobs (id, job_type, payload, status, max_retries, scheduled_at)
                VALUES (?, ?, ?, 'pending', ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status='pending',
                    payload=excluded.payload,
                    max_retries=excluded.max_retries,
                    scheduled_at=excluded.scheduled_at,
                    updated_at=CURRENT_TIMESTAMP
            """
            await db.conn.execute(query, (tid, job_type, payload_json, max_retries, sched_str))
            await db.conn.commit()

        # Update in-memory active tasks tracking
        filename = payload.get("filename", "Belge")
        update_task_status(
            tid,
            "pending",
            0,
            f"Kalıcı görev kuyruğuna alındı: {filename}",
            log_state="INFO",
        )

        log_event(
            "task",
            "INFO",
            f"Görev kalıcı kuyruğa eklendi [{job_type}]: {tid}",
            task_id=tid,
        )
        self._wake_event.set()
        return tid

    async def claim_next_job(self) -> dict | None:
        """Atomically claim the next eligible pending job using UPDATE ... RETURNING."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        claim_query = """
            UPDATE durable_jobs
            SET status = 'processing',
                started_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (
                SELECT id FROM durable_jobs
                WHERE status = 'pending' AND scheduled_at <= ?
                ORDER BY created_at ASC
                LIMIT 1
            )
            RETURNING id, job_type, payload, retry_count, max_retries
        """
        async with get_db_context() as db:
            try:
                cursor = await db.conn.execute(claim_query, (now_str,))
                row = await cursor.fetchone()
                await db.conn.commit()
                if not row:
                    return None

                return {
                    "id": row[0],
                    "job_type": row[1],
                    "payload": json.loads(row[2]) if row[2] else {},
                    "retry_count": row[3],
                    "max_retries": row[4],
                }
            except Exception as e:
                log_event("task", "ERROR", f"Job claim error: {e}")
                return None

    async def recover_orphaned_jobs(self) -> int:
        """Recover jobs left in 'processing' status due to application crash or power loss."""
        recovered = 0
        async with get_db_context() as db:
            cur = await db.conn.execute(
                "SELECT id, job_type, retry_count, max_retries FROM durable_jobs WHERE status = 'processing'"
            )
            orphans = await cur.fetchall()
            for r in orphans:
                job_id, _j_type, retries, max_r = r[0], r[1], r[2], r[3]
                if retries < max_r:
                    new_retries = retries + 1
                    await db.conn.execute(
                        """
                        UPDATE durable_jobs
                        SET status = 'pending',
                            retry_count = ?,
                            message = 'Çökme sonrası otomatik kurtarıldı',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (new_retries, job_id),
                    )
                    log_event(
                        "system",
                        "WARNING",
                        f"Yarım kalan görev kurtarıldı ve yeniden kuyruğa alındı: {job_id} (Deneme {new_retries}/{max_r})",
                        task_id=job_id,
                    )
                    recovered += 1
                else:
                    # Move directly to Dead-Letter Queue (DLQ)
                    await db.conn.execute(
                        """
                        UPDATE durable_jobs
                        SET status = 'dead',
                            error = 'Sistem çökmesi sonrası maksimum deneme sınırı aşıldı (DLQ)',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (job_id,),
                    )
                    log_event(
                        "system",
                        "ERROR",
                        f"Çöken görev DLQ'ya taşındı (Maksimum deneme aşıldı): {job_id}",
                        task_id=job_id,
                    )
            await db.conn.commit()
        return recovered

    async def record_success(self, task_id: str, message: str = "Başarıyla tamamlandı") -> None:
        """Mark durable job as successfully completed."""
        async with get_db_context() as db:
            await db.conn.execute(
                """
                UPDATE durable_jobs
                SET status = 'completed',
                    progress = 100,
                    message = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (message, task_id),
            )
            await db.conn.commit()

    async def _retry_job(
        self, db: Any, task_id: str, error_msg: str, new_retries: int, max_retries: int
    ) -> None:
        """Schedule job retry with exponential backoff delay."""
        delay_sec = min(60, (2**new_retries) * 2)
        next_run = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
        next_str = next_run.strftime("%Y-%m-%d %H:%M:%S")

        msg = f"Hata sonrası {delay_sec}s içinde tekrar denenecek ({new_retries}/{max_retries})"
        await db.conn.execute(
            """
            UPDATE durable_jobs
            SET status = 'pending',
                retry_count = ?,
                scheduled_at = ?,
                error = ?,
                message = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_retries, next_str, error_msg, msg, task_id),
        )
        update_task_status(task_id, "pending", 0, msg, log_state="WARNING")
        log_event(
            "task",
            "WARNING",
            f"Görev tekrar denenecek: {task_id} ({new_retries}/{max_retries}) | {error_msg}",
        )

    async def _move_to_dlq(self, db: Any, task_id: str, error_msg: str, max_retries: int) -> None:
        """Relegate permanently failed job to Dead-Letter Queue (DLQ)."""
        dlq_err = f"Maksimum deneme aşıldı ({max_retries}): {error_msg}"
        await db.conn.execute(
            """
            UPDATE durable_jobs
            SET status = 'dead',
                error = ?,
                message = 'Görev kalıcı olarak başarısız oldu (DLQ)',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (dlq_err, task_id),
        )
        update_task_status(task_id, "error", 100, dlq_err, log_state="error")
        log_event("task", "ERROR", f"Görev DLQ'ya aktarıldı: {task_id} | {dlq_err}")
        notify_ws("task_dead", {"task_id": task_id, "error": dlq_err})

    async def record_failure(
        self, task_id: str, error_msg: str, retry_count: int, max_retries: int
    ) -> None:
        """Handle job failure with exponential backoff retry or DLQ relegation."""
        new_retries = retry_count + 1
        async with get_db_context() as db:
            if new_retries <= max_retries:
                await self._retry_job(db, task_id, error_msg, new_retries, max_retries)
            else:
                await self._move_to_dlq(db, task_id, error_msg, max_retries)
            await db.conn.commit()

    async def get_job(self, task_id: str) -> dict | None:
        """Get job metadata and status by task ID."""
        async with get_db_context() as db:
            cur = await db.conn.execute(
                "SELECT id, job_type, payload, status, progress, message, error, retry_count, max_retries, created_at, updated_at FROM durable_jobs WHERE id = ?",
                (task_id,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "job_type": row[1],
                "payload": json.loads(row[2]) if row[2] else {},
                "status": row[3],
                "progress": row[4],
                "message": row[5],
                "error": row[6],
                "retry_count": row[7],
                "max_retries": row[8],
                "created_at": row[9],
                "updated_at": row[10],
            }

    async def _process_single_job(self, job: dict) -> None:
        """Process a claimed job with its registered handler."""
        task_id = job["id"]
        job_type = job["job_type"]
        retry_count = job["retry_count"]
        max_retries = job["max_retries"]

        handler = self._handlers.get(job_type)
        if not handler:
            log_event(
                "task",
                "ERROR",
                f"Bilinmeyen görev türü için işleyici bulunamadı: {job_type}",
            )
            await self.record_failure(
                task_id,
                f"No handler registered for {job_type}",
                retry_count,
                max_retries,
            )
            return

        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(job)
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self._executor, handler, job)

            await self.record_success(task_id, "İşlem başarıyla tamamlandı")
        except Exception as ex:
            log_event("task", "ERROR", f"Görev yürütme hatası ({task_id}): {ex}")
            await self.record_failure(task_id, str(ex), retry_count, max_retries)

    async def worker_loop(self) -> None:
        """Background continuous worker loop processing durable jobs."""
        self._running = True
        log_event("system", "INFO", "DurableTaskQueue worker loop başlatıldı")

        # Step 1: Recover any orphaned jobs from past crashes
        try:
            recovered_count = await self.recover_orphaned_jobs()
            if recovered_count > 0:
                log_event(
                    "system",
                    "INFO",
                    f"Açılışta {recovered_count} adet yarım kalmış görev kurtarıldı",
                )
        except Exception as rec_err:
            log_event("system", "ERROR", f"Orphan job recovery hatası: {rec_err}")

        # Step 2: Main polling & execution loop
        while self._running:
            try:
                job = await self.claim_next_job()
                if not job:
                    # No pending job ready; wait on wake event or 1.5s poll interval
                    try:
                        await asyncio.wait_for(self._wake_event.wait(), timeout=1.5)
                        self._wake_event.clear()
                    except asyncio.TimeoutError:
                        continue
                    continue

                await self._process_single_job(job)

            except asyncio.CancelledError:
                log_event("system", "INFO", "DurableTaskQueue worker loop durduruluyor...")
                raise
            except Exception as loop_err:
                log_event("system", "ERROR", f"DurableTaskQueue döngü hatası: {loop_err}")
                await asyncio.sleep(0.5)

    def shutdown(self, wait: bool = True) -> None:
        """Signal worker to stop and shutdown the thread pool."""
        self._running = False
        self._wake_event.set()
        try:
            self._executor.shutdown(wait=wait, cancel_futures=True)
        except TypeError:
            self._executor.shutdown(wait=wait)
