import asyncio
import os
from unittest.mock import patch

import pytest

from app.database import get_db_context

pytestmark = pytest.mark.asyncio


async def test_integration_flow(test_data_dir, sample_pdf_bytes):
    """Test full integration flow from PDF Upload simulation to Database storage with Mocking.

    After the ProcessPoolExecutor refactor, the heavy PDF processing pipeline
    lives in ``app.task_queue._process_pdf_in_worker``.  This test bypasses
    the ProcessPoolExecutor entirely by patching ``loop.run_in_executor`` to
    return the mock result directly — simulating what the worker process would
    produce without actually spawning a subprocess.
    """

    task_id = "test-task-123"
    filename = "yapay_zeka_devrimi.pdf"
    file_hash = "fakehash1234567890abcdef"

    # Save a temporary mock PDF file
    tmp_path = os.path.join(test_data_dir, "temp_uploaded.pdf")
    with open(tmp_path, "wb") as f:
        f.write(sample_pdf_bytes)

    # 1. Mock the AI analysis result that would come from the worker process
    mock_ai_result = {
        "kitap_adi": "Yapay Zeka Devrimi",
        "yazar": "Kai-Fu Lee",
        "kategori": "Teknoloji",
        "alt_kategori": "Yapay Zeka",
        "ozet": "Yapay zekanın küresel etkilerini ve geleceğini anlatan derinlemesine bir kitap incelemesi.",
        "anahtar_kelimeler": "yapay zeka, teknoloji, gelecek, çin, silikon vadisi",
    }

    # Build the result dict that _process_pdf_in_worker would return
    import shutil

    from app.constants import LIBRARY_ROOT
    from app.utils import sanitize_dirname, sanitize_filename

    kategori = sanitize_dirname(mock_ai_result.get("kategori", "Bilinmeyen"))
    dest_dir = os.path.join(LIBRARY_ROOT, kategori)
    os.makedirs(dest_dir, exist_ok=True)
    final_path = os.path.join(dest_dir, sanitize_filename(filename))
    shutil.copy2(tmp_path, final_path)

    mock_worker_result = {
        "data": mock_ai_result,
        "text_for_rag": "Mocked PDF Text content for analysis.",
        "final_path": final_path,
    }

    # 2. Patch run_in_executor to bypass ProcessPoolExecutor entirely.
    #    For the worker process dispatch (executor != None), return mock result.
    #    For asyncio.to_thread calls (executor == None), run the function normally.
    async def mock_run_in_executor(executor, fn, *args):
        """Return mock result for ProcessPoolExecutor; run normally for to_thread."""
        if executor is not None:
            # This is the ProcessPoolExecutor call for _process_pdf_in_worker
            return mock_worker_result
        else:
            # This is asyncio.to_thread (used for embedding) — execute normally
            return fn(*args)

    with patch.object(
        asyncio.get_event_loop(), "run_in_executor", side_effect=mock_run_in_executor
    ) as mock_executor:
        from app.task_queue import TaskQueue
        from app.tasks import active_tasks

        # Set up the task entry (normally done by the upload endpoint)
        active_tasks[task_id] = {
            "filename": filename,
            "status": "processing",
            "percentage": 0,
            "log_message": "Kuyrukta bekliyor...",
        }

        task_queue = TaskQueue()

        # Enqueue the job
        await task_queue.enqueue(
            {
                "task_id": task_id,
                "tmp_path": tmp_path,
                "filename": filename,
                "file_hash": file_hash,
                "provider": "gemini",
                "api_key": "fake-api-key",
                "config": {},
                "model_name": None,
                "base_url": None,
            }
        )

        # Run the worker loop for one iteration
        worker_task = asyncio.create_task(task_queue.worker_loop())
        await asyncio.sleep(0.5)  # Give the worker time to process
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

        task_queue.shutdown()

        # 3. Assertions
        # run_in_executor is called twice: once for the ProcessPoolExecutor
        # worker and once for asyncio.to_thread (embedding). Both are expected.
        # RAG embedding was removed from upload pipeline as planned
        assert mock_executor.call_count == 1  # Embedding was triggered

        # 4. Database Validation
        async with get_db_context() as db:
            assert await db.book_exists(file_hash)

            books_res = await db.get_all_books()
            books = books_res["items"]

            assert len(books) == 1
            book = books[0]
            assert book["kitap_adi"] == "Yapay Zeka Devrimi"
            assert book["yazar"] == "Kai-Fu Lee"

            # The category gets normalized from "Teknoloji" to "Bilim ve Teknoloji" by standard category mapping
            assert book["kategori"] == "Bilim ve Teknoloji"
            assert book["alt_kategori"] == "Yapay Zeka"
            assert book["dosya_hash"] == file_hash
            assert book["dosya_adi"] == filename

            # Fetch the physical file path dynamically
            db_path_res = await db.get_book_path(file_hash)
            assert db_path_res is not None
            dosya_yolu = db_path_res[0]

            # Destination path assertion
            assert os.path.exists(dosya_yolu)
            assert dosya_yolu.endswith(filename)
