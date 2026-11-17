"""Comprehensive regression tests for security, Turkish Unicode, EPUB/TXT reader, and PDF safety fixes."""

import io
import os
import time
import zipfile

import pytest

from app.auth import AUTH_COOKIE_NAME, AUTH_STATE
from app.config import is_safe_tesseract_executable
from app.constants import LIBRARY_ROOT
from app.services.handoff_service import _HANDOFF_LOCK, _HANDOFF_TOKENS, create_handoff_token
from app.services.pdf_compressor import PDFCompressorService
from app.utils import (
    looks_like_epub,
    looks_like_txt,
    resolve_portable_book_path,
    sanitize_export_stem,
    sanitize_filename,
)


class TestSecurityAndAuthFixes:
    """Verify auth bypass, Turkish UTF-8 password digest, and RCE validation fixes."""

    @pytest.mark.asyncio
    async def test_invalid_handoff_token_never_mints_auth_session(self, async_client):
        AUTH_STATE["valid_tokens"].clear()
        res = await async_client.get("/handoff/forged_invalid_token_999", follow_redirects=False)
        assert res.status_code == 302
        assert res.headers.get("location") == "/"
        assert AUTH_COOKIE_NAME not in res.cookies
        assert len(AUTH_STATE["valid_tokens"]) == 0

    @pytest.mark.asyncio
    async def test_valid_vs_expired_handoff_token(self, async_client):
        AUTH_STATE["valid_tokens"].clear()
        token = create_handoff_token("a" * 64, 12)

        res_ok = await async_client.get(f"/handoff/{token}", follow_redirects=False)
        assert res_ok.status_code == 302
        assert f"open_book={'a' * 64}" in res_ok.headers.get("location", "")
        assert "page=12" in res_ok.headers.get("location", "")
        assert AUTH_COOKIE_NAME in res_ok.cookies
        assert len(AUTH_STATE["valid_tokens"]) == 1

        # Expired handoff token must NOT mint a session
        with _HANDOFF_LOCK:
            _HANDOFF_TOKENS[token]["expires_at"] = time.time() - 10

        res_expired = await async_client.get(f"/handoff/{token}", follow_redirects=False)
        assert res_expired.status_code == 302
        assert res_expired.headers.get("location") == "/"
        assert AUTH_COOKIE_NAME not in res_expired.cookies
        assert len(AUTH_STATE["valid_tokens"]) == 1

    @pytest.mark.asyncio
    async def test_turkish_utf8_password_login_does_not_crash(self, async_client, monkeypatch):
        monkeypatch.setenv("ACCESS_PASSWORD", "Şifreğüşıöçİ123!")
        AUTH_STATE["attempts"].clear()
        AUTH_STATE["valid_tokens"].clear()

        # Cross-origin CSRF login attempt must be rejected with 403
        res_csrf = await async_client.post(
            "/api/auth/login",
            json={"password": "Şifreğüşıöçİ123!"},
            headers={"Origin": "https://evil-attacker.example.com"},
        )
        assert res_csrf.status_code == 403

        res_wrong = await async_client.post(
            "/api/auth/login",
            json={"password": "YanlışTürkçeŞifreİıÖç"},
            headers={"Origin": "http://test"},
        )
        assert res_wrong.status_code == 401
        assert AUTH_COOKIE_NAME not in res_wrong.cookies

        res_right = await async_client.post(
            "/api/auth/login",
            json={"password": "Şifreğüşıöçİ123!"},
            headers={"Origin": "http://test"},
        )
        assert res_right.status_code == 200
        assert AUTH_COOKIE_NAME in res_right.cookies

    @pytest.mark.asyncio
    async def test_tesseract_executable_validation_blocks_arbitrary_binaries(self, async_client):
        assert is_safe_tesseract_executable("") is True
        assert is_safe_tesseract_executable(r"C:\Program Files\Tesseract-OCR\tesseract.exe") is True
        assert is_safe_tesseract_executable("/usr/bin/tesseract") is True
        assert is_safe_tesseract_executable(r"C:\Windows\System32\cmd.exe") is False
        assert is_safe_tesseract_executable(r"\\evil-server\share\tesseract.exe") is False

        res = await async_client.post(
            "/api/settings",
            json={"tesseract_cmd": r"C:\Windows\System32\powershell.exe"},
        )
        assert res.status_code == 400


class TestUtilsAndPortablePaths:
    """Verify Turkish filename preservation, strict EPUB/TXT magic checks, and portable paths."""

    def test_sanitize_filename_preserves_turkish_and_blocks_reserved(self):
        cleaned = sanitize_filename("İhsan Oktay Anar - Puslu Kıtalar Atlası.pdf")
        assert "İhsan" in cleaned
        assert "Kıtalar" in cleaned
        assert cleaned.endswith(".pdf")

        reserved = sanitize_filename("CON.pdf")
        assert reserved.upper() != "CON.PDF"

        assert sanitize_export_stem("Kitap_Adı.pdf") == "Kitap_Adı"
        assert sanitize_export_stem("Notlar.EPUB") == "Notlar"

    def test_strict_epub_and_txt_detection(self):
        # Fake OOXML docx zip must NOT pass looks_like_epub
        fake_docx = io.BytesIO()
        with zipfile.ZipFile(fake_docx, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
        assert looks_like_epub(fake_docx.getvalue()) is False

        # Valid EPUB zip with META-INF/container.xml passes
        real_epub = io.BytesIO()
        with zipfile.ZipFile(real_epub, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", "<container/>")
        assert looks_like_epub(real_epub.getvalue()) is True

        # Binary with null bytes must NOT pass looks_like_txt
        assert looks_like_txt(b"hello\x00world\x00binary") is False
        # CP1254 Turkish text passes
        cp1254_bytes = "Çağdaş Türkçe edebiyatı üzerine düşünceler.".encode("cp1254")
        assert looks_like_txt(cp1254_bytes) is True

    def test_portable_book_path_reanchoring(self):
        os.makedirs(LIBRARY_ROOT, exist_ok=True)
        real_book = os.path.join(LIBRARY_ROOT, "tasinabilir_test.pdf")
        with open(real_book, "wb") as f:
            f.write(b"%PDF-1.4 portable test")

        stale_moved_path = r"D:\EskiBilgisayar\Masaustu\kutuphane\veriler\Dijital_Kutuphane\tasinabilir_test.pdf"
        resolved = resolve_portable_book_path(stale_moved_path, LIBRARY_ROOT)
        assert resolved != ""
        assert os.path.realpath(resolved) == os.path.realpath(real_book)

        # Traversal attempts must be rejected
        bad = resolve_portable_book_path(r"D:\x\Dijital_Kutuphane\..\..\secret.ini", LIBRARY_ROOT)
        assert bad == ""


class TestStructuredReaderAndSafeCompressor:
    """Verify native EPUB/TXT reader pagination endpoint and non-destructive PDF compression."""

    @pytest.mark.asyncio
    async def test_epub_and_turkish_txt_reader_content_endpoint(self, temp_db, async_client):
        os.makedirs(LIBRARY_ROOT, exist_ok=True)

        # 1. Synthetic multi-chapter EPUB
        epub_hash = "e" * 64
        epub_path = os.path.join(LIBRARY_ROOT, "ornek_eser.epub")
        with zipfile.ZipFile(epub_path, "w") as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr(
                "META-INF/container.xml",
                '<?xml version="1.0"?>'
                '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>'
                "</container>",
            )
            zf.writestr(
                "OEBPS/content.opf",
                '<?xml version="1.0" encoding="utf-8"?>'
                '<package xmlns="http://www.idpf.org/2007/opf" version="2.0">'
                "<manifest>"
                '<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>'
                "</manifest>"
                '<spine><itemref idref="ch1"/></spine>'
                "</package>",
            )
            zf.writestr(
                "OEBPS/ch1.xhtml",
                "<html><body><h1>Birinci Bölüm: Giriş</h1>"
                "<p>İslam felsefesi ve çağdaş düşünce tarihi üzerine kapsamlı bir inceleme.</p>"
                "</body></html>",
            )

        await temp_db.add_book(
            {
                "dosya_hash": epub_hash,
                "dosya_yolu": epub_path,
                "dosya_adi": "ornek_eser.epub",
                "kitap_adi": "Örnek EPUB Eseri",
                "yazar": "Test Yazarı",
                "kategori": "Felsefe",
            }
        )

        res_epub = await async_client.get(f"/api/books/{epub_hash}/reader-content")
        assert res_epub.status_code == 200
        epub_data = res_epub.json()
        assert epub_data["format"] == "epub"
        assert epub_data["total_pages"] >= 1
        assert any(
            "Birinci Bölüm" in str(b.get("text", "")) for b in epub_data["pages"][0]["blocks"]
        )
        assert len(epub_data["toc"]) >= 1

        # 2. Turkish CP1254 TXT
        txt_hash = "f" * 64
        txt_path = os.path.join(LIBRARY_ROOT, "turkce_notlar.txt")
        with open(txt_path, "wb") as f:
            f.write(
                "BÖLÜM 1\n\nŞüphe ve hakikat arayışında ğüşıöçĞÜŞİÖÇ karakter testi.".encode(
                    "cp1254"
                )
            )

        await temp_db.add_book(
            {
                "dosya_hash": txt_hash,
                "dosya_yolu": txt_path,
                "dosya_adi": "turkce_notlar.txt",
                "kitap_adi": "Türkçe Notlar",
                "yazar": "Test",
                "kategori": "Genel",
            }
        )

        res_txt = await async_client.get(f"/api/books/{txt_hash}/reader-content")
        assert res_txt.status_code == 200
        txt_data = res_txt.json()
        assert txt_data["format"] == "txt"
        assert txt_data["total_pages"] >= 1
        combined = " ".join(b["text"] for b in txt_data["pages"][0]["blocks"])
        assert "ğüşıöçĞÜŞİÖÇ" in combined

    @pytest.mark.asyncio
    async def test_compressor_protects_selectable_digital_vector_pdf(self):
        from reportlab.pdfgen import canvas as rl_canvas

        os.makedirs(LIBRARY_ROOT, exist_ok=True)
        vec_pdf = os.path.join(LIBRARY_ROOT, "digital_vector_book.pdf")
        c = rl_canvas.Canvas(vec_pdf)
        for p in range(3):
            c.drawString(72, 720, f"Page {p + 1}: Selectable digital vector typography content " * 4)
            c.drawString(
                72, 690, "This PDF already contains crisp selectable vector text streams. " * 4
            )
            c.showPage()
        c.save()

        original_bytes = os.path.getsize(vec_pdf)
        result = await PDFCompressorService.compress_pdf(vec_pdf)
        assert result["success"] is True
        assert result["optimized"] is False
        assert result["original_bytes"] == original_bytes
        assert os.path.getsize(vec_pdf) == original_bytes
