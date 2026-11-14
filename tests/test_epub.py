"""Unit tests for app.epub module."""

import os
import zipfile
from io import BytesIO

from PIL import Image

from app.constants import THUMBNAILS_DIR
from app.epub import (
    clean_html_content,
    extract_cover_from_epub,
    extract_text_from_epub,
    extract_text_from_txt,
)


def test_clean_html_content_empty():
    """clean_html_content should return empty string for falsy input."""
    assert clean_html_content("") == ""
    assert clean_html_content(None) == ""


def test_clean_html_content_scripts_and_styles():
    """clean_html_content should strip script and style tags and their contents."""
    raw = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>alert('xss');</script>
        </head>
        <body>
            <p>Gerçek metin burada.</p>
        </body>
    </html>
    """
    cleaned = clean_html_content(raw)
    assert "color: red" not in cleaned
    assert "alert" not in cleaned
    assert "Gerçek metin burada." in cleaned


def test_clean_html_content_entities():
    """clean_html_content should decode HTML entities."""
    raw = "<p>Kitap &amp; Sanat &mdash; &quot;Felsefe&#39;nin İlkeleri&quot; &lt;1. Cilt&gt;</p>"
    cleaned = clean_html_content(raw)
    assert 'Kitap & Sanat — "Felsefe\'nin İlkeleri" <1. Cilt>' == cleaned


def test_clean_html_content_block_tags():
    """clean_html_content should convert block tags to newlines and collapse whitespace."""
    raw = "<h1>Başlık</h1><p>Paragraf 1</p><div>Paragraf 2</div>"
    cleaned = clean_html_content(raw)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    assert lines == ["Başlık", "Paragraf 1", "Paragraf 2"]


def test_extract_text_from_txt(tmp_path):
    """extract_text_from_txt should handle UTF-8, ISO-8859-9, and CP1254 encodings."""
    # 1. UTF-8
    turkish_text = "Şiirler ve Öyküler: Çağdaş Türk Edebiyatı İncelemesi."
    utf8_file = tmp_path / "test_utf8.txt"
    utf8_file.write_text(turkish_text, encoding="utf-8")
    assert extract_text_from_txt(str(utf8_file)) == turkish_text

    # 2. Latin-1 / CP1254
    cp1254_file = tmp_path / "test_cp1254.txt"
    cp1254_file.write_bytes(turkish_text.encode("cp1254"))
    extracted = extract_text_from_txt(str(cp1254_file))
    assert "Şiirler" in extracted
    assert "Türk Edebiyatı" in extracted

    # 3. Non-existent file
    assert extract_text_from_txt(str(tmp_path / "non_existent.txt")) == ""

    # 4. Max chars limit
    assert len(extract_text_from_txt(str(utf8_file), max_chars=10)) == 10


def create_synthetic_epub(path: str, include_cover: bool = True):
    """Helper to generate a valid, minimal EPUB archive for testing."""
    with zipfile.ZipFile(path, "w") as z:
        # container.xml
        container_xml = """<?xml version="1.0"?>
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
           <rootfiles>
              <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
           </rootfiles>
        </container>"""
        z.writestr("META-INF/container.xml", container_xml)

        # cover image
        if include_cover:
            img_byte_arr = BytesIO()
            img = Image.new("RGB", (300, 450), color=(73, 109, 137))
            img.save(img_byte_arr, format="JPEG")
            z.writestr("OEBPS/cover.jpg", img_byte_arr.getvalue())

        # content.opf
        content_opf = """<?xml version="1.0" encoding="utf-8"?>
        <package xmlns="http://www.idpf.org/2007/opf" version="2.0">
          <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
            <dc:title>Test EPUB Kitap</dc:title>
            <meta name="cover" content="cover-image"/>
          </metadata>
          <manifest>
            <item id="cover-image" href="cover.jpg" media-type="image/jpeg"/>
            <item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
            <item id="ch2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
          </manifest>
          <spine>
            <itemref idref="ch1"/>
            <itemref idref="ch2"/>
          </spine>
        </package>"""
        z.writestr("OEBPS/content.opf", content_opf)

        # chapters
        ch1 = """<html xmlns="http://www.w3.org/1999/xhtml">
        <body>
            <h1>Bölüm 1: Başlangıç</h1>
            <p>Bu, EPUB ayrıştırıcısının test edilmesi için yazılmış birinci paragraftır.</p>
        </body></html>"""
        ch2 = """<html xmlns="http://www.w3.org/1999/xhtml">
        <body>
            <h1>Bölüm 2: Gelişme</h1>
            <p>İkinci bölüm metni de başarıyla ayrıştırılmalıdır.</p>
        </body></html>"""
        z.writestr("OEBPS/chapter1.xhtml", ch1)
        z.writestr("OEBPS/chapter2.xhtml", ch2)


def test_extract_text_from_epub(tmp_path):
    """extract_text_from_epub should read chapters in spine order."""
    epub_file = str(tmp_path / "book.epub")
    create_synthetic_epub(epub_file, include_cover=False)

    text = extract_text_from_epub(epub_file)
    assert "Bölüm 1: Başlangıç" in text
    assert "Bölüm 2: Gelişme" in text
    assert text.find("Bölüm 1") < text.find("Bölüm 2")

    # Max chars limit
    short_text = extract_text_from_epub(epub_file, max_chars=20)
    assert len(short_text) <= 20

    # Non-existent file
    assert extract_text_from_epub(str(tmp_path / "missing.epub")) == ""


def test_extract_cover_from_epub(tmp_path):
    """extract_cover_from_epub should extract cover image and save thumbnail as JPEG."""
    epub_file = str(tmp_path / "book_with_cover.epub")
    create_synthetic_epub(epub_file, include_cover=True)

    file_hash = "epub_test_cover_hash_12345"
    success = extract_cover_from_epub(epub_file, file_hash)
    assert success is True

    cover_jpg = os.path.join(THUMBNAILS_DIR, f"{file_hash}.jpg")
    assert os.path.exists(cover_jpg)

    # Clean up thumbnail
    try:
        os.remove(cover_jpg)
    except OSError:
        pass


def test_extract_cover_from_epub_no_cover(tmp_path):
    """extract_cover_from_epub should return False when no cover is present."""
    epub_file = str(tmp_path / "book_no_cover.epub")
    with zipfile.ZipFile(epub_file, "w") as z:
        z.writestr("text.html", "<p>No cover here</p>")

    file_hash = "epub_no_cover_hash"
    success = extract_cover_from_epub(epub_file, file_hash)
    assert success is False
