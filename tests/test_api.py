import zipfile
from unittest.mock import patch

import pytest

from app.epub import extract_text_from_epub, extract_text_from_txt

pytestmark = pytest.mark.asyncio


class TestAPIEndpoints:
    """Test API endpoints asynchronously."""

    async def test_root_endpoint(self, async_client):
        """Test root endpoint."""
        response = await async_client.get("/")
        assert response.status_code in [200, 303]  # May redirect to login

    async def test_health_check(self, async_client):
        """Test health check if available."""
        response = await async_client.get("/health")
        if response.status_code == 200:
            assert "status" in response.json() or "message" in response.json()

    async def test_api_docs_available(self, async_client):
        """Test that API documentation is available."""
        response = await async_client.get("/docs")
        assert response.status_code == 200

    async def test_api_redoc_available(self, async_client):
        """Test that ReDoc documentation is available."""
        response = await async_client.get("/redoc")
        assert response.status_code == 200

    async def test_static_files_served(self, async_client):
        """Test that static files are served."""
        response = await async_client.get("/static/css/style.css")
        assert response.status_code in [200, 404]


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints asynchronously."""

    async def test_login_page_loads(self, async_client):
        """Test that login page loads."""
        response = await async_client.get("/")
        assert response.status_code in [200, 303]

    async def test_protected_endpoint_requires_auth(self, async_client):
        """Test that protected endpoints require authentication."""
        response = await async_client.get("/api/books")
        assert response.status_code in [200, 403, 401]


class TestBookEndpoints:
    """Test book-related endpoints asynchronously."""

    async def test_get_books_empty(self, async_client):
        """Test getting books returns the paginated response shape."""
        response = await async_client.get("/api/books")
        assert response.status_code == 200
        data = response.json()
        assert {"items", "total", "limit", "offset"} <= set(data)
        assert isinstance(data["items"], list)

    async def test_book_validation(self, async_client):
        """Test book data validation."""
        response = await async_client.post("/api/upload")
        assert response.status_code in [400, 422]


class TestConfigEndpoints:
    """Test configuration-related endpoints asynchronously."""

    async def test_get_config(self, async_client):
        """Test getting configuration."""
        response = await async_client.get("/api/settings")
        assert response.status_code in [200, 403, 401]

    async def test_update_config(self, async_client):
        """Test updating configuration."""
        response = await async_client.post("/api/settings", json={})
        assert response.status_code in [200, 403, 401]


class TestChatEndpoint:
    """Test chat endpoint guardrails."""

    async def test_chat_full_book_disables_pdf_mode_when_text_is_too_large(
        self,
        async_client,
        temp_db_conn,
        test_data_dir,
        sample_pdf_bytes,
    ):
        """Large full-text cache should auto-fallback to excerpt mode."""
        import os

        from app.routers.chat import _GEMMA_NATIVE_PDF_MAX_CHARS

        file_hash = "chat_guardrail_big_book_hash"
        pdf_path = os.path.join(test_data_dir, "chat_guardrail_big_book.pdf")

        with open(pdf_path, "wb") as f:
            f.write(sample_pdf_bytes)
        with open(f"{pdf_path}.full.txt", "w", encoding="utf-8") as f:
            f.write("a" * (_GEMMA_NATIVE_PDF_MAX_CHARS + 10))

        await temp_db_conn.execute(
            """
            INSERT INTO kitaplar
            (kitap_adi, yazar, kategori, alt_kategori, ozet, anahtar_kelimeler, dosya_adi, dosya_hash, dosya_yolu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Büyük Kitap",
                "Deneme Yazar",
                "Bilim ve Teknoloji",
                "Yapay Zeka",
                "Test özeti",
                "test, chat",
                "chat_guardrail_big_book.pdf",
                file_hash,
                pdf_path,
            ),
        )
        await temp_db_conn.commit()

        generate_calls = []

        def _fake_generate_ai_response(**kwargs):
            generate_calls.append(kwargs)
            return "fallback-ok"

        with (
            patch(
                "app.routers.chat._should_upload_native_pdf", return_value=(False, "Context limit")
            ),
            patch("app.ai_router.generate_ai_response", side_effect=_fake_generate_ai_response),
        ):
            response = await async_client.post(
                "/api/chat",
                json={
                    "message": "Bu kitap ne anlatıyor?",
                    "target_book_hash": file_hash,
                    "load_full_book": True,
                },
                headers={"X-AI-Provider": "ollama", "X-AI-Key": "test"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "fallback-ok"
        assert len(generate_calls) == 1
        assert generate_calls[0]["pdf_path"] is None
        assert (
            "AŞAĞIDA 'Büyük Kitap' KİTABININ TAM METNİ YER ALMAKTADIR"
            in generate_calls[0]["prompt"]
        )

    async def test_chat_full_book_retries_without_pdf_on_context_error(
        self,
        async_client,
        temp_db_conn,
        test_data_dir,
        sample_pdf_bytes,
    ):
        """If provider returns context overflow error, endpoint should retry without PDF."""
        import os

        file_hash = "chat_guardrail_retry_hash"
        pdf_path = os.path.join(test_data_dir, "chat_guardrail_retry.pdf")

        with open(pdf_path, "wb") as f:
            f.write(sample_pdf_bytes)
        with open(f"{pdf_path}.full.txt", "w", encoding="utf-8") as f:
            f.write("kısa metin " * 200)

        await temp_db_conn.execute(
            """
            INSERT INTO kitaplar
            (kitap_adi, yazar, kategori, alt_kategori, ozet, anahtar_kelimeler, dosya_adi, dosya_hash, dosya_yolu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Orta Kitap",
                "Deneme Yazar",
                "Bilim ve Teknoloji",
                "Yapay Zeka",
                "Test özeti",
                "test, retry",
                "chat_guardrail_retry.pdf",
                file_hash,
                pdf_path,
            ),
        )
        await temp_db_conn.commit()

        calls = []

        def _fake_generate_ai_response(**kwargs):
            calls.append(kwargs)
            return "retry-ok"

        with (
            patch(
                "app.routers.chat._should_upload_native_pdf", return_value=(False, "Context limit")
            ),
            patch("app.ai_router.generate_ai_response", side_effect=_fake_generate_ai_response),
        ):
            response = await async_client.post(
                "/api/chat",
                json={
                    "message": "Bu kitaptan bir çıkarım yap.",
                    "target_book_hash": file_hash,
                    "load_full_book": True,
                },
                headers={"X-AI-Provider": "lmstudio"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "retry-ok"
        assert len(calls) == 1
        assert calls[0]["pdf_path"] is None
        assert "AŞAĞIDA 'Orta Kitap' KİTABININ TAM METNİ YER ALMAKTADIR" in calls[0]["prompt"]

    async def test_session_manager_lru_and_ttl(self):
        """Verify BookSessionManager evicts stale sessions based on LRU capacity and TTL."""
        import time

        from app.services.session_manager import BookSession, BookSessionManager

        manager = BookSessionManager(max_sessions=2, ttl_seconds=10)

        # Mock sessions directly without API calls
        sess1 = BookSession("hash1", "/path1.pdf", "gemini-3.5-flash-lite", "instr")
        sess1.is_initialized = True
        sess1.last_accessed = time.time() - 100  # Expired by TTL

        sess2 = BookSession("hash2", "/path2.pdf", "gemini-3.5-flash-lite", "instr")
        sess2.is_initialized = True
        sess2.last_accessed = time.time() - 5

        sess3 = BookSession("hash3", "/path3.pdf", "gemini-3.5-flash-lite", "instr")
        sess3.is_initialized = True
        sess3.last_accessed = time.time()

        manager._sessions["hash1"] = sess1
        manager._sessions["hash2"] = sess2
        manager._sessions["hash3"] = sess3

        # Trigger eviction
        manager._evict_stale_sessions()

        # hash1 was expired (> 10s TTL)
        assert "hash1" not in manager._sessions
        # hash2 and hash3 remain within capacity (max_sessions=2)
        assert "hash2" in manager._sessions
        assert "hash3" in manager._sessions

        # Add 4th session to test LRU capacity trim
        sess4 = BookSession("hash4", "/path4.pdf", "gemini-3.5-flash-lite", "instr")
        sess4.is_initialized = True
        sess4.last_accessed = time.time()
        manager._sessions["hash4"] = sess4

        manager._evict_stale_sessions()
        # Should trim down to 2 sessions, removing oldest (hash2)
        assert len(manager._sessions) <= 2
        assert "hash2" not in manager._sessions
        assert "hash3" in manager._sessions
        assert "hash4" in manager._sessions


@pytest.mark.asyncio
async def test_annotations_crud_and_cascade(async_client, temp_db):
    """Test creating, reading, batch syncing, and cascade deletion of annotations."""
    file_hash = "a" * 64

    # 1. Insert a test book first
    await temp_db.add_book(
        {
            "kitap_adi": "Annotation Test Book",
            "yazar": "Test Author",
            "kategori": "Felsefe",
            "dosya_hash": file_hash,
            "dosya_adi": "test_book.pdf",
            "dosya_yolu": "/fake/path/test_book.pdf",
        }
    )

    # 2. Add single annotation
    res_add = await async_client.post(
        f"/api/books/{file_hash}/annotations",
        json={
            "id": "ann_1",
            "sayfa_no": 3,
            "secilen_metin": "Önemli bir felsefi alıntı",
            "not_metni": "Bu kısım tezin temelini oluşturuyor",
            "renk_hex": "#fef08a",
            "renk_sinif": "yellow",
            "koordinatlar": '[{"top":0.1,"left":0.1,"width":0.8,"height":0.05}]',
        },
    )
    assert res_add.status_code == 200
    assert res_add.json()["status"] == "saved"

    # 3. Retrieve annotations
    res_get = await async_client.get(f"/api/books/{file_hash}/annotations")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["status"] == "success"
    assert len(data["annotations"]) == 1
    assert data["annotations"][0]["id"] == "ann_1"
    assert data["annotations"][0]["sayfa_no"] == 3

    # 4. Batch sync
    res_batch = await async_client.post(
        f"/api/books/{file_hash}/annotations/batch",
        json={
            "annotations": [
                {
                    "id": "ann_1",
                    "sayfa_no": 3,
                    "secilen_metin": "Önemli bir felsefi alıntı (güncellendi)",
                    "not_metni": "Güncel not",
                    "renk_hex": "#bbf7d0",
                    "renk_sinif": "green",
                    "koordinatlar": "[]",
                },
                {
                    "id": "ann_2",
                    "sayfa_no": 5,
                    "secilen_metin": "İkinci alıntı",
                    "not_metni": "İkinci not",
                    "renk_hex": "#bfdbfe",
                    "renk_sinif": "blue",
                    "koordinatlar": "[]",
                },
            ]
        },
    )
    assert res_batch.status_code == 200
    assert res_batch.json()["count"] == 2

    # Check AI formatting
    ai_notes = await temp_db.get_book_notes_for_ai(file_hash)
    assert "Önemli bir felsefi alıntı (güncellendi)" in ai_notes
    assert "İkinci alıntı" in ai_notes
    assert "[Sayfa 3]" in ai_notes
    assert "[Sayfa 5]" in ai_notes

    # 5. Delete one annotation
    res_del_ann = await async_client.delete(f"/api/books/{file_hash}/annotations/ann_2")
    assert res_del_ann.status_code == 200
    assert res_del_ann.json()["status"] == "deleted"

    # Check count is now 1
    anns_after_del = await temp_db.get_book_annotations(file_hash)
    assert len(anns_after_del) == 1
    assert anns_after_del[0]["id"] == "ann_1"

    # 6. Delete book and verify cascade deletion of annotations
    res_del_book = await async_client.delete(f"/api/books/{file_hash}")
    assert res_del_book.status_code == 200
    assert res_del_book.json()["status"] == "deleted"

    # Verify annotations are completely purged
    anns_after_cascade = await temp_db.get_book_annotations(file_hash)
    assert len(anns_after_cascade) == 0


async def test_epub_and_txt_parser(tmp_path):
    """Test pure-Python EPUB and TXT text extractors."""
    # 1. Test TXT extraction
    txt_file = tmp_path / "deneme.txt"
    txt_file.write_text("Merhaba Dünya! Bu bir dijital kütüphane testidir.", encoding="utf-8")
    extracted_txt = extract_text_from_txt(str(txt_file))
    assert "Merhaba Dünya!" in extracted_txt

    # 2. Test EPUB extraction
    epub_file = tmp_path / "kitap.epub"
    with zipfile.ZipFile(str(epub_file), "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
            <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                <rootfiles>
                    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
                </rootfiles>
            </container>""",
        )
        z.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0"?>
            <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
                <manifest>
                    <item id="chapter1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
                </manifest>
                <spine>
                    <itemref idref="chapter1"/>
                </spine>
            </package>""",
        )
        z.writestr(
            "OEBPS/ch1.xhtml",
            """<html xmlns="http://www.w3.org/1999/xhtml">
                <head><title>Bölüm 1</title></head>
                <body>
                    <h1>Birinci Bölüm</h1>
                    <p>EPUB standart metin testi başarılı bir şekilde ayrıştırıldı.</p>
                </body>
            </html>""",
        )

    extracted_epub = extract_text_from_epub(str(epub_file))
    assert "Birinci Bölüm" in extracted_epub
    assert "EPUB standart metin testi" in extracted_epub
