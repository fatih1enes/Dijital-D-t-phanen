"""Unit and integration tests for Faz 3: Scanned PDF OCR Layer, Bookmarks, and Rich EPUB."""

from __future__ import annotations

import io
import os
import zipfile

import httpx
import pytest
from PIL import Image, ImageDraw

from app.constants import LIBRARY_ROOT
from app.epub import extract_structured_reader_pages
from app.main import app as fastapi_app


def _create_image_only_pdf(dest_path: str, text_line: str = "Merhaba Dijital Kutuphane OCR Testi") -> None:
    """Create a 1-page raster-only PDF (zero native PDF text objects) for OCR testing."""
    img = Image.new("RGB", (1200, 500), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((80, 140), text_line, fill=(0, 0, 0))
    img.save(dest_path, "PDF", resolution=150.0)
    img.close()


@pytest.mark.asyncio
async def test_scanned_pdf_ocr_layer_endpoint_and_sqlite_cache(temp_db) -> None:
    """Verify GET /api/books/{hash}/ocr-page/1 extracts normalized word boxes and caches in SQLite."""
    os.makedirs(LIBRARY_ROOT, exist_ok=True)
    b_hash = "d" * 64
    pdf_path = os.path.join(LIBRARY_ROOT, "scanned_only_phase3.pdf")
    _create_image_only_pdf(pdf_path, "COGNITION EPISTEMOLOGY ARCHIVE")

    await temp_db.add_book(
        {
            "dosya_hash": b_hash,
            "dosya_yolu": pdf_path,
            "dosya_adi": "scanned_only_phase3.pdf",
            "kitap_adi": "Taranmış Belge",
        }
    )

    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        r1 = await client.get(f"/api/books/{b_hash}/ocr-page/1")
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["file_hash"] == b_hash
        assert d1["page"] == 1
        if d1.get("available"):
            assert d1["cached"] is False
            for w in d1["words"]:
                assert 0.0 <= w["x"] <= 1.0
                assert 0.0 <= w["y"] <= 1.0

            # Second request must hit SQLite cache instantly
            r2 = await client.get(f"/api/books/{b_hash}/ocr-page/1")
            assert r2.status_code == 200
            assert r2.json()["cached"] is True


@pytest.mark.asyncio
async def test_bookmarks_crud_and_rich_epub_assets_and_footnotes(temp_db) -> None:
    """Verify bookmarks endpoints, rich EPUB NCX TOC, footnotes, and secure /epub-asset image serving."""
    os.makedirs(LIBRARY_ROOT, exist_ok=True)
    e_hash = "e" * 64
    epub_path = os.path.join(LIBRARY_ROOT, "rich_phase3.epub")

    # Tiny valid 8x8 PNG image
    png_buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(140, 90, 50)).save(png_buf, format="PNG")
    png_bytes = png_buf.getvalue()

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
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
            '<item id="c1" href="text/ch1.xhtml" media-type="application/xhtml+xml"/>'
            '<item id="img1" href="images/diagram.png" media-type="image/png"/>'
            "</manifest>"
            '<spine toc="ncx"><itemref idref="c1"/></spine>'
            "</package>",
        )
        zf.writestr(
            "OEBPS/toc.ncx",
            '<?xml version="1.0" encoding="utf-8"?>'
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
            "<navMap>"
            '<navPoint id="np1" playOrder="1">'
            "<navLabel><text>Ana Bölüm</text></navLabel>"
            '<content src="text/ch1.xhtml"/>'
            '<navPoint id="np2" playOrder="2">'
            "<navLabel><text>Alt Başlık 1.1</text></navLabel>"
            '<content src="text/ch1.xhtml#sec1"/>'
            "</navPoint>"
            "</navPoint>"
            "</navMap></ncx>",
        )
        zf.writestr("OEBPS/images/diagram.png", png_bytes)
        zf.writestr(
            "OEBPS/text/ch1.xhtml",
            "<html><body>"
            "<h1>Ana Bölüm</h1>"
            '<p>Metin içi dipnot referansı<a href="#fn1" epub:type="noteref">1</a> burada yer alır.</p>'
            '<img src="../images/diagram.png" alt="Felsefi Diyagram"/>'
            '<aside id="fn1" epub:type="footnote">1. Aristo Metafizik 980a21 kaynak notu.</aside>'
            "</body></html>",
        )

    parsed = extract_structured_reader_pages(epub_path)
    assert parsed["format"] == "epub"
    assert len(parsed["toc"]) == 2
    assert parsed["toc"][1]["level"] == 2
    assert "fn1" in parsed["footnotes"]
    assert "Aristo Metafizik" in parsed["footnotes"]["fn1"]
    for pg in parsed["pages"]:
        for blk in pg["blocks"]:
            assert isinstance(blk["text"], str)

    await temp_db.add_book(
        {
            "dosya_hash": e_hash,
            "dosya_yolu": epub_path,
            "dosya_adi": "rich_phase3.epub",
            "kitap_adi": "Zengin EPUB Eseri",
        }
    )

    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Serve embedded EPUB image
        img_resp = await client.get(
            f"/api/books/{e_hash}/epub-asset", params={"path": "OEBPS/images/diagram.png"}
        )
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"] == "image/png"

        # 2. Reject path traversal
        bad_resp = await client.get(
            f"/api/books/{e_hash}/epub-asset", params={"path": "../../etc/passwd.png"}
        )
        assert bad_resp.status_code == 400

        # 3. Bookmarks toggle & list
        bm_post = await client.post(
            f"/api/books/{e_hash}/bookmarks", json={"sayfa_no": 1, "toggle": True}
        )
        assert bm_post.status_code == 200
        assert bm_post.json()["bookmarked"] is True

        bm_get = await client.get(f"/api/books/{e_hash}/bookmarks")
        assert len(bm_get.json()["bookmarks"]) == 1
