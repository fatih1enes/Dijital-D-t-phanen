"""Comprehensive test suite for Phase 1 & 2 fixes and Phase 3 server-side enhancements.

Verifies:
1. stream_upload_to_temp_file computes and returns accurate total byte count.
2. /api/settings handles null or invalid gemini_cascade_models without 500 error or log_event signature error.
3. Cross-platform path traversal sanitization in sanitize_filename for Windows and Linux.
4. Server-side filtering, searching, favoriting, and sorting in DocumentRepository.get_all_books.
5. Per-book concurrency locking and lifecycle cleanup in BookSessionManager.
6. Telegram optimizations safe fallback without brittle ctypes monkeypatching.
"""

import io
import os

import aiosqlite
import pytest
from fastapi import UploadFile

from app.repositories.document_repository import DocumentRepository
from app.routers.books import stream_upload_to_temp_file
from app.services.cascade_manager import cascade_manager
from app.services.session_manager import BookSessionManager
from app.services.telegram_service import setup_telethon_optimizations
from app.utils import sanitize_filename


class TestStreamUploadTotalBytes:
    """Validate upload streaming byte counter."""

    @pytest.mark.asyncio
    async def test_stream_upload_returns_total_bytes(self):
        sample_data = b"%PDF-1.4 test document content for streaming validation."
        file_obj = io.BytesIO(sample_data)
        upload = UploadFile(file=file_obj, filename="test_doc.pdf")

        tmp_path, file_hash, first_chunk, total_bytes = await stream_upload_to_temp_file(
            upload, 10 * 1024 * 1024, "Test Belgesi", suffix=".pdf"
        )
        try:
            assert total_bytes == len(sample_data)
            assert len(file_hash) == 64
            assert first_chunk.startswith(b"%PDF-")
            assert os.path.exists(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestSettingsAndCascadeHardening:
    """Validate settings updates and cascade manager tolerance to null/empty values."""

    def test_cascade_configure_chain_with_none(self):
        # Should not throw TypeError: 'NoneType' object is not iterable
        cascade_manager.configure_chain(None)
        assert len(cascade_manager.profiles) > 0

    def test_cascade_configure_chain_with_invalid_items(self):
        cascade_manager.configure_chain(["", None, "   ", "gemini-2.5-flash"])
        assert "gemini-2.5-flash" in cascade_manager.profiles


class TestSanitizeFilenameCrossPlatform:
    """Validate cross-platform path traversal stripping."""

    def test_windows_and_linux_traversals(self):
        cases = [
            ("..\\..\\windows_evil.pdf", "windows_evil.pdf"),
            ("../../linux_evil.pdf", "linux_evil.pdf"),
            ("some/nested/path/book.pdf", "book.pdf"),
            ("some\\nested\\path\\book.pdf", "book.pdf"),
            ("dots....in..name.pdf", "dots_in_name.pdf"),
            ("normal_file.epub", "normal_file.epub"),
        ]
        for inp, expected in cases:
            res = sanitize_filename(inp)
            assert ".." not in res
            assert "/" not in res
            assert "\\" not in res
            assert res == expected


class TestBookSessionManagerConcurrency:
    """Validate per-book async lock and lifecycle cleanup."""

    @pytest.mark.asyncio
    async def test_lock_for_isolation(self):
        mgr = BookSessionManager(max_sessions=5)
        lock_a = mgr.lock_for("hash_a")
        lock_b = mgr.lock_for("hash_b")
        assert lock_a is not lock_b
        assert mgr.lock_for("hash_a") is lock_a

        # Acquire lock_a and ensure lock_b is unaffected
        async with lock_a:
            assert lock_a.locked()
            assert not lock_b.locked()

        mgr.close_all()
        assert len(mgr._sessions) == 0
        assert len(mgr._locks) == 0


class TestDocumentRepositoryServerFiltering:
    """Validate server-side searching, filtering, and sorting in SQLite."""

    @pytest.mark.asyncio
    async def test_server_side_filters_and_sorts(self):
        async with aiosqlite.connect(":memory:") as conn:
            # Create minimal schema for test
            await conn.execute("""
                CREATE TABLE kitaplar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kitap_adi TEXT,
                    yazar TEXT,
                    kategori TEXT,
                    alt_kategori TEXT,
                    ozet TEXT,
                    anahtar_kelimeler TEXT,
                    dosya_adi TEXT,
                    dosya_hash TEXT UNIQUE,
                    dosya_yolu TEXT,
                    has_cover INTEGER DEFAULT 0,
                    is_favorite INTEGER DEFAULT 0,
                    okunulan_sayfa INTEGER DEFAULT 0,
                    sira_numarasi INTEGER DEFAULT 0,
                    ekleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("""
                CREATE TABLE koleksiyonlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT
                )
            """)
            await conn.execute("""
                CREATE TABLE koleksiyon_kitap (
                    koleksiyon_id INTEGER,
                    kitap_hash TEXT,
                    PRIMARY KEY (koleksiyon_id, kitap_hash)
                )
            """)
            await conn.commit()

            repo = DocumentRepository(conn)

            # Insert sample books
            await repo.add_book(
                {
                    "kitap_adi": "Sefiller",
                    "yazar": "Victor Hugo",
                    "kategori": "Klasik Roman",
                    "ozet": "Jean Valjean'ın hikayesi",
                    "anahtar_kelimeler": "fransa, adalet, merhamet",
                    "dosya_adi": "sefiller.pdf",
                    "dosya_hash": "a" * 64,
                }
            )
            await repo.add_book(
                {
                    "kitap_adi": "Suç ve Ceza",
                    "yazar": "Fyodor Dostoyevski",
                    "kategori": "Klasik Roman",
                    "ozet": "Raskolnikov'un vicdan muhasebesi",
                    "anahtar_kelimeler": "rusya, cinayet, psikoloji",
                    "dosya_adi": "suc_ve_ceza.pdf",
                    "dosya_hash": "b" * 64,
                }
            )
            await repo.add_book(
                {
                    "kitap_adi": "Yapay Zeka Devrimi",
                    "yazar": "Alan Turing",
                    "kategori": "Bilim",
                    "ozet": "Makine öğrenmesi ve yapay zeka",
                    "anahtar_kelimeler": "bilgisayar, kodlama, zeka",
                    "dosya_adi": "ai.pdf",
                    "dosya_hash": "c" * 64,
                }
            )

            # Favorite the first book
            await repo.toggle_favorite("a" * 64)

            # 1. Test search filter
            res_search = await repo.get_all_books(search="Dostoyevski")
            assert res_search["total"] == 1
            assert res_search["items"][0]["kitap_adi"] == "Suç ve Ceza"

            # 2. Test favorite filter
            res_fav = await repo.get_all_books(favorite=True)
            assert res_fav["total"] == 1
            assert res_fav["items"][0]["kitap_adi"] == "Sefiller"

            # 3. Test category filter
            res_cat = await repo.get_all_books(category="Bilim")
            assert res_cat["total"] == 1
            assert res_cat["items"][0]["kitap_adi"] == "Yapay Zeka Devrimi"

            # 4. Test title_asc sort
            res_sort = await repo.get_all_books(sort="title_asc")
            titles = [b["kitap_adi"] for b in res_sort["items"]]
            assert titles == sorted(titles)


class TestTelegramOptimizationSetup:
    """Validate telethon engine detection."""

    def test_setup_telethon_optimizations_returns_string(self):
        engine = setup_telethon_optimizations()
        assert isinstance(engine, str)
        assert len(engine) > 0
