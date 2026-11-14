"""Tests for R&D Audit V9 enhancements: Concurrency, Security, EPUB, Logging, and WebSockets."""

import json
from unittest.mock import MagicMock

import pytest
from starlette.datastructures import Headers

from app.auth import _is_local_request
from app.epub import _decode_epub_bytes, clean_html_content
from app.logger import LOG_BUFFER, log_event


class TestAuditV9Enhancements:
    """Validate V9 R&D optimizations and security guards."""

    @pytest.mark.asyncio
    async def test_annotations_batch_repository(self, temp_db):
        """Verify save_book_annotations_batch saves annotations in a single atomic batch."""
        test_hash = "v9_hash_" + "0" * 56
        await temp_db.add_book(
            {
                "dosya_hash": test_hash,
                "dosya_yolu": "/fake/path.pdf",
                "dosya_adi": "test_v9.pdf",
                "kitap_adi": "Test V9 Book",
                "yazar": "Author",
                "kategori": "Test",
                "has_cover": False,
            }
        )

        annotations = [
            {
                "id": f"ann_{i}",
                "dosya_hash": test_hash,
                "sayfa_no": i + 1,
                "secilen_metin": f"Metin {i}",
                "not_metni": f"Not {i}",
                "renk_hex": "#fef08a",
                "renk_sinif": "yellow",
                "koordinatlar": "[]",
            }
            for i in range(5)
        ]

        count = await temp_db.save_book_annotations_batch(annotations)
        assert count == 5

        saved = await temp_db.get_book_annotations(test_hash)
        assert len(saved) == 5

    @pytest.mark.asyncio
    async def test_v9_indexes_present_in_database(self, temp_db_conn):
        """Verify composite and case-insensitive indexes exist in sqlite_master."""
        cursor = await temp_db_conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        rows = await cursor.fetchall()
        index_names = {r[0] for r in rows}

        assert "idx_kitaplar_sira_tarih" in index_names
        assert "idx_kitaplar_dosya_adi_nocase" in index_names

    def test_is_local_request_spoofing_defense(self):
        """Verify remote request sending X-Forwarded-For: 127.0.0.1 cannot spoof local auth."""
        mock_req = MagicMock()
        mock_req.client.host = "192.168.1.150"
        mock_req.headers = Headers({"x-forwarded-for": "127.0.0.1"})

        assert _is_local_request(mock_req) is False

    def test_epub_unescape_and_turkish_decoding(self):
        """Verify HTML entity unescaping and Turkish encoding cascade in EPUB module."""
        # 1. HTML entities
        raw_html = "<p>T&#252;rkiye &amp; &#304;stanbul &ldquo;Kitap&rdquo; &#8230;</p>"
        cleaned = clean_html_content(raw_html)
        assert "Türkiye" in cleaned
        assert "İstanbul" in cleaned
        assert "&" in cleaned
        assert "Kitap" in cleaned

        # 2. Windows-1254 encoded Turkish bytes
        raw_tr_bytes = "Değişiklik ve Çalışma".encode("windows-1254")
        decoded = _decode_epub_bytes(raw_tr_bytes)
        assert "Değişiklik" in decoded
        assert "Çalışma" in decoded

    def test_logger_sensitive_data_masking(self):
        """Verify sensitive API keys are automatically masked before entering LOG_BUFFER."""
        LOG_BUFFER.clear()
        raw_key = "AIzaSy" + "A" * 33
        entry = log_event("test", "INFO", f"Error connecting with key {raw_key}")

        assert raw_key not in entry["message"]
        assert "AIzaSy[MASKED]" in entry["message"]

        # Verify entry in ring buffer is also masked
        assert len(LOG_BUFFER) > 0
        assert raw_key not in LOG_BUFFER[-1]["message"]

    def test_websocket_ping_pong(self):
        """Verify WebSocket /ws endpoint responds to ping with pong."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps({"type": "ping"}))
            reply_text = ws.receive_text()
            reply = json.loads(reply_text)
            assert reply.get("type") == "pong"

    @pytest.mark.asyncio
    async def test_find_duplicate_books_repository(self, temp_db):
        """Verify find_duplicate_books groups books by identical title & author or size & pages."""
        # Add 2 books with same title and author
        await temp_db.add_book(
            {
                "dosya_hash": "dup_hash_1",
                "dosya_yolu": "/fake/dup1.pdf",
                "dosya_adi": "dup1.pdf",
                "kitap_adi": "Sefiller",
                "yazar": "Victor Hugo",
                "dosya_boyutu": 100000,
                "sayfa_sayisi": 500,
            }
        )
        await temp_db.add_book(
            {
                "dosya_hash": "dup_hash_2",
                "dosya_yolu": "/fake/dup2.pdf",
                "dosya_adi": "dup2.pdf",
                "kitap_adi": "Sefiller",
                "yazar": "Victor Hugo",
                "dosya_boyutu": 105000,
                "sayfa_sayisi": 502,
            }
        )
        # Add 1 unique book
        await temp_db.add_book(
            {
                "dosya_hash": "unique_hash",
                "dosya_yolu": "/fake/unique.pdf",
                "dosya_adi": "unique.pdf",
                "kitap_adi": "Karamazov Kardeşler",
                "yazar": "Dostoyevski",
                "dosya_boyutu": 200000,
                "sayfa_sayisi": 800,
            }
        )

        duplicates = await temp_db.find_duplicate_books()
        assert len(duplicates) >= 1
        group = duplicates[0]
        assert group["title"] == "Sefiller"
        assert len(group["items"]) == 2

    def test_pwa_manifest_and_sw_assets(self):
        """Verify PWA manifest.json and sw.js exist and are valid."""
        import json
        import os

        manifest_path = os.path.join("static", "manifest.json")
        sw_path = os.path.join("static", "sw.js")

        assert os.path.exists(manifest_path), "manifest.json must exist"
        assert os.path.exists(sw_path), "sw.js must exist"

        with open(manifest_path, encoding="utf-8") as f:
            manifest_data = json.load(f)

        assert manifest_data.get("name") == "Dijital Kütüphane"
        assert manifest_data.get("display") == "standalone"
        assert len(manifest_data.get("icons", [])) > 0

    @pytest.mark.asyncio
    async def test_pdf_compressor_service_guard(self):
        """Verify PDFCompressorService handles missing files gracefully."""
        from app.services.pdf_compressor import PDFCompressorService

        service = PDFCompressorService()
        result = await service.compress_pdf("/non/existent/path.pdf")
        assert result["success"] is False
        assert "bulunamadı" in result["message"]
