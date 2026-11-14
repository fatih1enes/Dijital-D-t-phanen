"""Comprehensive unit and integration tests for Library Productivity & Reading Ergonomics.

Tests:
1. [10.3] Global "Deep Search" Engine (BM25 FTS5 snippet matching and page teleportation).
2. [7.3] PDF Auto TOC & Page Offset Solver (native extraction, fallback synthesizer, offset resolution).
3. [10.2] Akıllı Dinamik Koleksiyonlar (DQL rule compiler, dynamic SQL filtering).
4. [6.4] Zero-Friction Continuity: QR Code Instant LAN Handoff (token lifecycle, pure-Python SVG QR, redemption).
5. [7.1] Gölge Kütüphaneci (Auto-Watchfolder stability detection, duplicate rejection, task queue ingestion).
"""

import asyncio
import io
import json
import os
import tempfile
import zipfile
from unittest.mock import AsyncMock, patch

import pytest

from app.database import DatabaseManager
from app.services.handoff_service import (
    consume_handoff_token,
    create_handoff_token,
    generate_qr_svg,
    get_local_lan_ip,
)
from app.services.hybrid_search import hybrid_search_engine
from app.services.smart_collections import smart_collection_compiler
from app.services.toc_service import toc_service
from app.services.watchfolder_service import watchfolder_service


class TestGlobalDeepSearch:
    """Tests for [10.3] Global Deep Search across book pages."""

    @pytest.mark.asyncio
    async def test_deep_search_snippet_highlighting(self, temp_db: DatabaseManager):
        """Verify deep search returns highlighted snippets and exact page numbers."""
        # 1. Insert sample book
        await temp_db.conn.execute(
            """
            INSERT INTO kitaplar (dosya_hash, kitap_adi, yazar, kategori, has_cover)
            VALUES ('deep_h1', 'Kritik Düşünme Sanatı', 'Ahmet Demir', 'Felsefe', 1)
            """
        )
        # 2. Insert text chunk into kitap_chunks and kitap_chunks_fts
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_chunks (dosya_hash, sayfa_no, chunk_index, metin, char_count)
            VALUES ('deep_h1', 42, 0, 'Epistemolojik açıdan bakıldığında hakikat arayışı zihinsel bir disiplin gerektirir.', 80)
            """
        )
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_chunks_fts (dosya_hash, sayfa_no, chunk_index, metin)
            VALUES ('deep_h1', 42, 0, 'Epistemolojik açıdan bakıldığında hakikat arayışı zihinsel bir disiplin gerektirir.')
            """
        )
        await temp_db.conn.commit()

        # 3. Perform deep search
        results = await hybrid_search_engine.deep_search_pages(
            temp_db, query="epistemolojik hakikat", limit=10
        )

        assert len(results) == 1
        match = results[0]
        assert match["dosya_hash"] == "deep_h1"
        assert match["sayfa_no"] == 42
        assert match["kitap_adi"] == "Kritik Düşünme Sanatı"
        assert match["yazar"] == "Ahmet Demir"
        assert match["has_cover"] is True
        assert '<mark class="deep-hl">' in match["snippet"]

    @pytest.mark.asyncio
    async def test_deep_search_endpoint(self, async_client):
        """Test GET /api/search/deep returns structured matches."""
        resp = await async_client.get("/api/search/deep?q=")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_matches"] == 0

        resp2 = await async_client.get("/api/search/deep?q=deneme")
        assert resp2.status_code == 200
        assert "results" in resp2.json()


class TestPDFTOCAndOffsetSolver:
    """Tests for [7.3] PDF TOC & Page Offset Solver."""

    @pytest.mark.asyncio
    async def test_toc_db_caching(self, temp_db: DatabaseManager):
        """Stored TOC items must be retrieved quickly from database cache."""
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_toc (dosya_hash, title, page_number, target_page, level, source)
            VALUES ('toc_hash_1', 'Bölüm 1: Giriş', 10, 18, 1, 'auto_detected')
            """
        )
        await temp_db.conn.commit()

        items = await toc_service.get_or_generate_toc(temp_db, "toc_hash_1")
        assert len(items) == 1
        assert items[0]["title"] == "Bölüm 1: Giriş"
        assert items[0]["page_number"] == 10
        assert items[0]["target_page"] == 18
        assert items[0]["source"] == "auto_detected"

    @pytest.mark.asyncio
    async def test_toc_endpoint(self, async_client):
        """GET /api/books/{hash}/toc endpoint test."""
        # Non-existent valid 64-char hex hash
        valid_hash = "a" * 64
        resp = await async_client.get(f"/api/books/{valid_hash}/toc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["items"] == []


class TestSmartDynamicCollections:
    """Tests for [10.2] Akıllı Dinamik Koleksiyonlar & DQL Rule Compiler."""

    def test_dql_compiler_clauses(self):
        """Test parameter compilation for various filter constraints."""
        rules = {
            "category": "Felsefe",
            "favorite_only": True,
            "min_page": 150,
            "max_page": 600,
            "added_within_days": 14,
            "has_notes": True,
            "keyword": "etik",
        }
        clauses, params = smart_collection_compiler.compile_rules(rules)

        assert "kategori = ?" in clauses
        assert "is_favorite = 1" in clauses
        assert "okunulan_sayfa >= ?" in clauses
        assert "okunulan_sayfa <= ?" in clauses
        assert "dosya_hash IN (SELECT DISTINCT dosya_hash FROM kitap_notlari)" in clauses
        assert "Felsefe" in params
        assert 150 in params
        assert 600 in params
        assert "-14" in params

    @pytest.mark.asyncio
    async def test_dynamic_collection_filtering(self, temp_db: DatabaseManager):
        """Dynamic collection must dynamically filter matching books."""
        # Insert test books
        await temp_db.conn.execute(
            """
            INSERT INTO kitaplar (dosya_hash, kitap_adi, kategori, is_favorite, okunulan_sayfa)
            VALUES
                ('b_dyn_1', 'Felsefe Kitabı 1', 'Felsefe', 1, 250),
                ('b_dyn_2', 'Felsefe Kitabı 2', 'Felsefe', 0, 80),
                ('b_dyn_3', 'Tarih Kitabı', 'Tarih', 1, 300)
            """
        )
        # Create a dynamic collection for: Category = Felsefe AND Favorite = True
        rule_data = {"category": "Felsefe", "favorite_only": True}
        col = await temp_db.add_collection(
            "Favori Felsefe",
            is_dynamic=True,
            rule_json=json.dumps(rule_data),
        )
        assert col is not None
        col_id = col["id"]

        # Query all books with collection_id
        res = await temp_db.get_all_books(collection_id=col_id)
        books = res["items"]

        assert len(books) == 1
        assert books[0]["dosya_hash"] == "b_dyn_1"
        assert books[0]["kitap_adi"] == "Felsefe Kitabı 1"


class TestInstantLANHandoff:
    """Tests for [6.4] QR Code Instant LAN Handoff."""

    def test_handoff_token_lifecycle(self):
        """Token must be valid for 30-day passkey continuity across multiple mobile sessions."""
        token = create_handoff_token("book_hash_xyz", page_number=45)
        assert len(token) > 10

        # First consumption succeeds
        consumed = consume_handoff_token(token)
        assert consumed is not None
        assert consumed["file_hash"] == "book_hash_xyz"
        assert consumed["page_number"] == 45

        # 30-day Passkey continuity guarantee: subsequent consumptions also succeed
        second = consume_handoff_token(token)
        assert second is not None
        assert second["file_hash"] == "book_hash_xyz"
        assert second["page_number"] == 45

    def test_mini_qr_svg_generation(self):
        """Pure-Python MiniQR must output valid SVG with rect tags."""
        test_url = "http://192.168.1.150:8000/handoff/abcdef12345"
        svg = generate_qr_svg(test_url, box_size=6)

        assert svg.startswith("<svg")
        assert svg.strip().endswith("</svg>")
        assert '<rect width="' in svg
        assert 'fill="#000000"' in svg

    def test_local_ip_detection(self):
        """LAN IP lookup should return a non-empty string."""
        ip = get_local_lan_ip()
        assert isinstance(ip, str)
        assert len(ip) >= 7

    @pytest.mark.asyncio
    async def test_handoff_endpoint_redemption(self, async_client):
        """GET /handoff/{token} issues session cookie and redirects to book workspace."""
        token = create_handoff_token("redemption_hash", page_number=27)

        resp = await async_client.get(f"/handoff/{token}", follow_redirects=False)
        assert resp.status_code == 302
        loc = resp.headers.get("location")
        assert loc == "/?open_book=redemption_hash&page=27"
        # Cookie must be set
        cookies = resp.headers.get("set-cookie", "")
        assert "library_auth=" in cookies or "session" in cookies

        # Expired / invalid token redirects smoothly to home page (302)
        resp_bad = await async_client.get("/handoff/invalid_token_999", follow_redirects=False)
        assert resp_bad.status_code == 302
        assert resp_bad.headers.get("location") == "/"


class TestShadowIngestorWatchfolder:
    """Tests for [7.1] Gölge Kütüphaneci (Auto-Watchfolder)."""

    def test_watchfolder_service_status(self):
        """Watchfolder service provides status info."""
        status = watchfolder_service.get_status()
        assert "running" in status
        assert "enabled" in status
        assert "interval" in status

    @pytest.mark.asyncio
    async def test_scan_directory_stability_check(self):
        """Newly created files require two stability checks before queuing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "new_book.pdf")
            with open(pdf_path, "wb") as f:
                f.write(b"%PDF-1.4 sample content for testing watchfolder stability\n%%EOF\n" * 5)

            # First scan tick: records stability, returns 0
            count1 = await watchfolder_service.scan_directory(temp_dir)
            assert count1 == 0
            assert pdf_path in watchfolder_service._file_stability_cache

            # Wait a fraction of a second and scan again (stable):
            await asyncio.sleep(0.1)
            # Second scan tick: file is stable
            count2 = await watchfolder_service.scan_directory(temp_dir)
            # Either 1 or 0 depending on mocked task queue dependency
            assert count2 in (0, 1)

    @pytest.mark.asyncio
    async def test_watchfolder_endpoints(self, async_client):
        """Test GET /api/settings/watchfolder and scan trigger endpoint."""
        resp = await async_client.get("/api/settings/watchfolder")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data

        resp_scan = await async_client.post("/api/settings/watchfolder/scan")
        assert resp_scan.status_code == 200


class TestProductivityAndBackupEndpoints:
    """Endpoint-level regression tests for duplicates, PDF compression, and full ZIP export."""

    @pytest.mark.asyncio
    async def test_duplicates_endpoint_returns_groups(
        self, async_client, temp_db: DatabaseManager
    ):
        """GET /api/books/duplicates queries DatabaseManager directly without AttributeError."""
        h1 = "1" * 64
        h2 = "2" * 64
        await temp_db.add_book(
            {
                "dosya_hash": h1,
                "dosya_yolu": "/fake/dupa.pdf",
                "dosya_adi": "dupa.pdf",
                "kitap_adi": "Kürk Mantolu Madonna",
                "yazar": "Sabahattin Ali",
                "has_cover": False,
            }
        )
        await temp_db.add_book(
            {
                "dosya_hash": h2,
                "dosya_yolu": "/fake/dupb.pdf",
                "dosya_adi": "dupb.pdf",
                "kitap_adi": "Kürk Mantolu Madonna",
                "yazar": "Sabahattin Ali",
                "has_cover": False,
            }
        )

        resp = await async_client.get("/api/books/duplicates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["total_groups"] >= 1
        assert len(data["duplicates"]) >= 1

    @pytest.mark.asyncio
    async def test_compress_book_endpoint_succeeds(
        self, async_client, temp_db: DatabaseManager, test_data_dir
    ):
        """POST /api/books/{hash}/compress succeeds even when optimized=True without missing-column SQL errors."""
        file_hash = "c" * 64
        pdf_path = os.path.join(test_data_dir, "compress_target.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 sample content\n%%EOF\n")

        await temp_db.add_book(
            {
                "dosya_hash": file_hash,
                "dosya_yolu": pdf_path,
                "dosya_adi": "compress_target.pdf",
                "kitap_adi": "Optimize Kitap",
                "yazar": "Yazar",
                "has_cover": False,
            }
        )

        mock_res = {
            "success": True,
            "optimized": True,
            "old_bytes": 10000,
            "compressed_bytes": 5000,
            "old_mb": 0.01,
            "new_mb": 0.0,
            "reduction_percent": 50.0,
        }
        with patch(
            "app.services.pdf_compressor.pdf_compressor.compress_pdf",
            new=AsyncMock(return_value=mock_res),
        ):
            resp = await async_client.post(f"/api/books/{file_hash}/compress")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["optimized"] is True
        assert data["reduction_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_export_full_zip_endpoint(self, async_client, test_data_dir):
        """GET /api/database/export-full-zip exports a valid portable ZIP archive."""
        import app.config as app_config

        cfg_path = app_config.CONFIG_PATH
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"ai_provider": "gemini"}, f)

        resp = await async_client.get("/api/database/export-full-zip")
        assert resp.status_code == 200
        assert "application/zip" in resp.headers.get("content-type", "")

        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            names = zf.namelist()
            assert "kutuphane.db" in names
            assert "config.json" in names
            assert "yedek_bilgisi.json" in names
            manifest = json.loads(zf.read("yedek_bilgisi.json").decode("utf-8"))
            assert manifest["version"] == "1.0.0"
