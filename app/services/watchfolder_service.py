"""Shadow Ingestor (Gölge Kütüphaneci): Background Auto-Watchfolder service."""

import asyncio
import os
import shutil
import tempfile
import time
import uuid
from typing import Any

from app.config import load_config, resolve_ai_credentials
from app.database import get_db_context
from app.logger import log_event, notify_ws
from app.tasks import active_tasks
from app.utils import get_file_hash_from_path


def _is_file_readable(path: str) -> bool:
    """Test if a file can be opened for reading without lock or sharing contention."""
    try:
        with open(path, "rb") as f:
            f.read(1024)
        return True
    except OSError:
        return False


def _get_scan_candidates(watch_dir: str) -> list[str]:
    """Scan directory and return list of supported candidate file paths."""
    candidates: list[str] = []
    with os.scandir(watch_dir) as entries:
        for entry in entries:
            if not entry.is_file():
                continue
            fname = entry.name.lower()
            if fname.startswith((".", "~$")) or fname.endswith((".crdownload", ".part", ".tmp")):
                continue
            if fname.endswith((".pdf", ".epub", ".txt")):
                candidates.append(entry.path)
    return candidates


class WatchfolderService:
    """Monitors configured directories and automatically queues new books without user friction."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running: bool = False
        self._file_stability_cache: dict[
            str, tuple[int, float, int]
        ] = {}  # path -> (size, mtime, stable_ticks)
        self._processed_hashes: set[str] = set()

    async def start(self) -> None:
        """Start the background watchfolder polling loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._watch_loop(), name="watchfolder_daemon")
        log_event("system", "INFO", "Gölge Kütüphaneci (Auto-Watchfolder) servisi başlatıldı.")
        await asyncio.sleep(0)

    async def stop(self) -> None:
        """Stop the background watchfolder loop safely."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                log_event("system", "DEBUG", "Watchfolder servisi durduruldu.")
        self._task = None

    def get_status(self) -> dict[str, Any]:
        """Return runtime status of the watchfolder service."""
        cfg = load_config()
        return {
            "running": self._running,
            "enabled": bool(cfg.get("watchfolder_enabled", False)),
            "path": str(cfg.get("watchfolder_path", "")),
            "interval": int(cfg.get("watchfolder_interval", 5)),
            "tracked_files": len(self._file_stability_cache),
        }

    async def _watch_loop(self) -> None:
        """Main loop that periodically checks the watchfolder."""
        while self._running:
            cfg = load_config()
            interval = int(cfg.get("watchfolder_interval", 5))
            try:
                if cfg.get("watchfolder_enabled"):
                    watch_dir = str(cfg.get("watchfolder_path", "")).strip()
                    if watch_dir and os.path.exists(watch_dir) and os.path.isdir(watch_dir):
                        await self.scan_directory(watch_dir)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log_event("watchfolder", "WARNING", f"Watchfolder tarama döngüsü uyarısı: {e}")

            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise

    def _is_candidate_stable(self, file_path: str, cur_size: int, cur_mtime: float) -> bool:
        """Check whether candidate file size and mtime are stable across consecutive scans."""
        if file_path not in self._file_stability_cache:
            self._file_stability_cache[file_path] = (cur_size, cur_mtime, 1)
            return False

        last_size, last_mtime, _ticks = self._file_stability_cache[file_path]
        if cur_size != last_size or abs(cur_mtime - last_mtime) > 0.5:
            self._file_stability_cache[file_path] = (cur_size, cur_mtime, 1)
            return False

        return True

    async def _process_single_candidate(self, file_path: str) -> bool:
        """Process a single file candidate for stability, hash uniqueness, and ingestion."""
        try:
            stat = os.stat(file_path)
            cur_size = stat.st_size
            cur_mtime = stat.st_mtime

            # Ensure file has content (> 100 bytes)
            if cur_size < 100:
                return False

            # File copy/write lock check: verify file can be opened and read without lock contention
            is_readable = await asyncio.to_thread(_is_file_readable, file_path)
            if not is_readable:
                return False

            # Stability check: size must remain unchanged across consecutive ticks
            if not self._is_candidate_stable(file_path, cur_size, cur_mtime):
                return False

            # File is stable! Check if hash already imported
            file_hash = await asyncio.to_thread(get_file_hash_from_path, file_path)
            if file_hash in self._processed_hashes:
                return False

            async with get_db_context() as db:
                existing = await db.get_book_path(file_hash)
                if existing and existing[0]:
                    self._processed_hashes.add(file_hash)
                    return False

            # New book found! Copy and queue ingestion
            success = await self._enqueue_ingestion(file_path, file_hash, cur_size)
            if success:
                self._processed_hashes.add(file_hash)
                return True
            return False
        except OSError as file_err:
            log_event(
                "watchfolder",
                "DEBUG",
                f"Dosya erişim uyarısı ({file_path}): {file_err}",
            )
            return False
        except Exception as ex:
            log_event(
                "watchfolder",
                "WARNING",
                f"Belge işleme uyarısı ({file_path}): {ex}",
            )
            return False

    async def scan_directory(self, watch_dir: str) -> int:
        """Scan target folder for complete, stable files and enqueue any new documents."""
        enqueued_count = 0
        try:
            candidates = _get_scan_candidates(watch_dir)
            for file_path in candidates:
                if await self._process_single_candidate(file_path):
                    enqueued_count += 1
        except Exception as e:
            log_event("watchfolder", "WARNING", f"Klasör taranırken hata: {e}")

        return enqueued_count

    async def _enqueue_ingestion(self, source_path: str, file_hash: str, file_size: int) -> bool:
        """Enqueue new file into the durable task queue."""
        from app.dependencies import get_task_queue

        task_queue = get_task_queue()
        if not task_queue:
            return False

        filename = os.path.basename(source_path)
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"wf_{file_hash[:12]}_{filename}")

        try:
            await asyncio.to_thread(shutil.copy2, source_path, tmp_path)
        except OSError as e:
            log_event("watchfolder", "ERROR", f"Dosya geçici alana kopyalanamadı: {e}")
            return False

        task_id = f"wf_{uuid.uuid4().hex[:8]}"
        now_ts = time.time()
        msg_text = "Gölge Kütüphaneci tarafından tespit edildi, kuyruğa alındı..."
        task_entry = {
            "filename": filename,
            "status": "processing",
            "state": "pending",
            "pct": 5,
            "percentage": 5,
            "msg": msg_text,
            "log_message": msg_text,
            "last_update": now_ts,
            "logs": [
                {
                    "ts": now_ts,
                    "message": f"Otomatik izleme klasöründen algılandı: {filename}",
                    "status": "processing",
                    "state": "pending",
                    "pct": 5,
                    "percentage": 5,
                }
            ],
        }
        active_tasks[task_id] = task_entry

        cfg = load_config()
        provider, api_key, model_name, base_url = resolve_ai_credentials()

        await task_queue.enqueue(
            {
                "task_id": task_id,
                "tmp_path": tmp_path,
                "filename": filename,
                "file_hash": file_hash,
                "provider": provider,
                "api_key": api_key,
                "config": cfg,
                "model_name": model_name,
                "base_url": base_url,
            }
        )

        log_event(
            "watchfolder",
            "INFO",
            f"Gölge Kütüphaneci: '{filename}' otomatik kütüphaneye alındı.",
            task_id=task_id,
            filename=filename,
            size_bytes=file_size,
        )
        notify_ws("task", {"task_id": task_id, "task": task_entry})
        return True


watchfolder_service = WatchfolderService()
