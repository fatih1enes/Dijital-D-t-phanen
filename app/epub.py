"""EPUB and text document parser module using standard Python libraries.

Provides robust, pure-Python text and cover extraction from .epub and .txt files
without external heavy dependencies.
"""

import html
import os
import re
import urllib.parse
from io import BytesIO
from typing import Any

try:
    import defusedxml.ElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET
import zipfile

from PIL import Image

from app.constants import MAX_COVER_BYTES, MAX_IMAGE_PIXELS, THUMBNAILS_DIR
from app.logger import log_event


def _decode_epub_bytes(data: bytes) -> str:
    """Decode EPUB raw bytes trying common Turkish and international encodings before fallback."""
    for enc in ("utf-8", "utf-8-sig", "windows-1254", "iso-8859-9", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def clean_html_content(raw_html: str) -> str:
    """Strip HTML/XML tags and unescape common entities into clean readable text."""
    if not raw_html:
        return ""
    # Remove script and style blocks
    cleaned = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE
    )
    # Replace block level tags with newlines
    cleaned = re.sub(r"<(p|div|h[1-6]|li|tr|br)[^>]*>", "\n", cleaned, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Robust standard unescape of all numeric and named HTML entities
    cleaned = html.unescape(cleaned)
    # Normalize multiple whitespace and newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    return cleaned.strip()


MAX_EPUB_ENTRY_BYTES = 20 * 1024 * 1024  # 20 MB ceiling to prevent decompression bombs


def safe_read_zip_entry(
    z: zipfile.ZipFile, entry_name: str, max_bytes: int = MAX_EPUB_ENTRY_BYTES
) -> bytes | None:
    """Safely read a zip entry, rejecting decompression bombs exceeding max_bytes."""
    try:
        info = z.getinfo(entry_name)
        if info.file_size > max_bytes:
            log_event(
                "epub",
                "WARNING",
                f"EPUB girdisi güvenlik limitini aşıyor ({info.file_size} > {max_bytes}), atlandı: {entry_name}",
            )
            return None
        return z.read(entry_name)
    except Exception as e:
        log_event("epub", "WARNING", f"EPUB girdisi okunamadı ({entry_name}): {e}")
        return None


def _locate_opf_path(z: zipfile.ZipFile) -> str:
    """Locate the root OPF metadata file inside an EPUB archive."""
    try:
        container_data = safe_read_zip_entry(z, "META-INF/container.xml", max_bytes=2 * 1024 * 1024)
        if container_data:
            root_container = ET.fromstring(container_data)
            rootfile = root_container.find(
                ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
            )
            if rootfile is not None and rootfile.attrib.get("full-path"):
                return rootfile.attrib["full-path"]
    except Exception as e:
        log_event("epub", "DEBUG", f"container.xml ayrıştırılamadı: {e}")

    for name in z.namelist():
        if name.lower().endswith(".opf"):
            return name
    return ""


def _resolve_entry_path(z: zipfile.ZipFile, opf_dir: str, href: str) -> str | None:
    """Resolve normalized or raw candidate path for an EPUB manifest item."""
    decoded_href = urllib.parse.unquote(href)
    full_entry_path = os.path.normpath(os.path.join(opf_dir, decoded_href)).replace("\\", "/")
    if full_entry_path in z.namelist():
        return full_entry_path

    raw_candidate = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
    if raw_candidate in z.namelist():
        return raw_candidate

    return None


def _parse_opf_manifest_and_spine(
    root_opf: Any,
) -> tuple[dict[str, str], list[str]]:
    """Parse manifest mapping and spine item references from OPF XML."""
    manifest = {}
    for item in root_opf.findall(".//{http://www.idpf.org/2007/opf}item"):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        if item_id and href:
            manifest[item_id] = href

    spine_idrefs = []
    for itemref in root_opf.findall(".//{http://www.idpf.org/2007/opf}itemref"):
        idref = itemref.attrib.get("idref")
        if idref and idref in manifest:
            spine_idrefs.append(idref)

    return manifest, spine_idrefs


def _extract_cleaned_entry_text(z: zipfile.ZipFile, entry_path: str) -> str | None:
    """Read, decode and strip HTML from a single zip entry."""
    raw_bytes = safe_read_zip_entry(z, entry_path, max_bytes=MAX_EPUB_ENTRY_BYTES)
    if not raw_bytes:
        return None
    raw = _decode_epub_bytes(raw_bytes)
    return clean_html_content(raw) or None


def _extract_text_from_spine(z: zipfile.ZipFile, opf_path: str, max_chars: int) -> list[str]:
    """Extract text sequentially following the EPUB spine order."""
    text_parts = []
    current_chars = 0
    opf_dir = os.path.dirname(opf_path)

    try:
        opf_data = safe_read_zip_entry(z, opf_path, max_bytes=5 * 1024 * 1024)
        if not opf_data:
            return []

        root_opf = ET.fromstring(opf_data)
        manifest, spine_idrefs = _parse_opf_manifest_and_spine(root_opf)

        for idref in spine_idrefs:
            full_entry_path = _resolve_entry_path(z, opf_dir, manifest[idref])
            if not full_entry_path:
                continue

            cleaned = _extract_cleaned_entry_text(z, full_entry_path)
            if cleaned:
                text_parts.append(cleaned)
                current_chars += len(cleaned)
                if max_chars > 0 and current_chars >= max_chars:
                    break
    except Exception as opf_err:
        log_event(
            "epub",
            "WARNING",
            f"OPF ayrıştırılamadı, doğrudan html taranıyor: {opf_err}",
        )

    return text_parts


def _extract_text_from_html_fallback(z: zipfile.ZipFile, max_chars: int) -> list[str]:
    """Fallback text extraction scanning raw html/xhtml entries in the zip."""
    text_parts = []
    current_chars = 0
    for name in sorted(z.namelist()):
        if not name.lower().endswith((".html", ".xhtml", ".htm")):
            continue
        try:
            cleaned = _extract_cleaned_entry_text(z, name)
            if cleaned:
                text_parts.append(cleaned)
                current_chars += len(cleaned)
                if max_chars > 0 and current_chars >= max_chars:
                    break
        except Exception as e:
            log_event("epub", "DEBUG", f"HTML fallback okuma hatası ({name}): {e}")
            continue
    return text_parts


def extract_text_from_epub(file_path: str, max_chars: int = 50000) -> str:
    """Extract clean reading text from an EPUB document following spine order."""
    if not os.path.exists(file_path):
        return ""

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            opf_path = _locate_opf_path(z)
            text_parts = _extract_text_from_spine(z, opf_path, max_chars) if opf_path else []

            if not text_parts:
                text_parts = _extract_text_from_html_fallback(z, max_chars)

            full_text = "\n\n".join(text_parts)
            if max_chars > 0 and len(full_text) > max_chars:
                return full_text[:max_chars]
            return full_text

    except Exception as e:
        log_event("epub", "ERROR", f"EPUB metin çıkarımı hatası ({file_path}): {e}")
        return ""


def _find_cover_href_in_opf(root_opf: Any) -> str | None:
    """Locate cover image href in OPF XML elements."""
    cover_id = None
    for meta in root_opf.findall(".//{http://www.idpf.org/2007/opf}meta"):
        if meta.attrib.get("name") == "cover":
            cover_id = meta.attrib.get("content")
            break

    if not cover_id:
        return None

    for item in root_opf.findall(".//{http://www.idpf.org/2007/opf}item"):
        if item.attrib.get("id") == cover_id:
            return item.attrib.get("href")

    return None


def _find_cover_in_single_opf(z: zipfile.ZipFile, opf_name: str) -> bytes | None:
    """Attempt reading cover image bytes from a single OPF manifest."""
    try:
        opf_data = safe_read_zip_entry(z, opf_name, max_bytes=5 * 1024 * 1024)
        if not opf_data:
            return None

        root_opf = ET.fromstring(opf_data)
        opf_dir = os.path.dirname(opf_name)
        href = _find_cover_href_in_opf(root_opf)
        if href:
            full_p = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
            if full_p in z.namelist():
                return safe_read_zip_entry(z, full_p, max_bytes=MAX_COVER_BYTES)
    except Exception as e:
        log_event("epub", "DEBUG", f"OPF kapak metaverisi okunamadı: {e}")
    return None


def _find_cover_in_opf(z: zipfile.ZipFile) -> bytes | None:
    """Search for cover image in OPF manifest across zip."""
    for name in z.namelist():
        if name.lower().endswith(".opf"):
            cover_data = _find_cover_in_single_opf(z, name)
            if cover_data:
                return cover_data
    return None


def _find_cover_in_candidates(z: zipfile.ZipFile) -> bytes | None:
    """Search for image entries matching cover keywords."""
    candidates = []
    for name in z.namelist():
        lower = name.lower()
        if lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
            if "cover" in lower:
                candidates.insert(0, name)
            else:
                candidates.append(name)

    if candidates:
        try:
            return safe_read_zip_entry(z, candidates[0], max_bytes=MAX_COVER_BYTES)
        except Exception as e:
            log_event("epub", "DEBUG", f"Kapak adayı okunamadı: {e}")
    return None


def _save_cover_thumbnail(cover_data: bytes, out_path: str) -> bool:
    """Validate, resize and save cover bytes to thumbnail file."""
    try:
        with Image.open(BytesIO(cover_data)) as img:
            if img.size[0] * img.size[1] > MAX_IMAGE_PIXELS:
                log_event(
                    "epub",
                    "WARNING",
                    "EPUB kapak görseli boyut sınırını aşıyor, atlandı.",
                )
                return False
            work = img.convert("RGB") if img.mode != "RGB" else img.copy()
            try:
                work.thumbnail((400, 560), Image.Resampling.LANCZOS)
                work.save(out_path, "JPEG", quality=88)
            finally:
                work.close()
        return True
    except Image.DecompressionBombError:
        log_event(
            "epub",
            "WARNING",
            "EPUB kapağı decompression bomb koruması nedeniyle reddedildi.",
        )
        return False
    except (OSError, SyntaxError, ValueError) as img_err:
        log_event("epub", "DEBUG", f"EPUB kapağı işlenemedi: {img_err}")
        return False


def extract_cover_from_epub(file_path: str, file_hash: str) -> bool:
    """Extract or generate a cover image from an EPUB archive and save as a thumbnail."""
    if not os.path.exists(file_path):
        return False

    os.makedirs(THUMBNAILS_DIR, exist_ok=True)
    out_path = os.path.join(THUMBNAILS_DIR, f"{file_hash}.jpg")

    try:
        with zipfile.ZipFile(file_path, "r") as z:
            cover_data = _find_cover_in_opf(z) or _find_cover_in_candidates(z)
            if cover_data:
                return _save_cover_thumbnail(cover_data, out_path)
    except Exception as e:
        log_event("epub", "WARNING", f"EPUB kapak çıkarımı başarısız: {e}")

    return False


def extract_text_from_txt(file_path: str, max_chars: int = 25000) -> str:
    """Read plain text files with multiple fallback encodings."""
    if not os.path.exists(file_path):
        return ""

    encodings = ["utf-8", "utf-8-sig", "cp1254", "iso-8859-9", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, encoding=enc) as f:
                if max_chars > 0:
                    return f.read(max_chars)
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            break

    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            if max_chars > 0:
                return f.read(max_chars)
            return f.read()
    except Exception:
        return ""


def _parse_html_blocks(raw_html: str) -> tuple[str, list[dict[str, str]]]:
    """Extract chapter heading and clean structured blocks (h1/h2/h3/blockquote/p) from EPUB XHTML."""
    import html as html_lib
    import re

    if not raw_html:
        return "", []

    cleaned = re.sub(r"<(script|style|head)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.I)
    title_match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", cleaned, flags=re.DOTALL | re.I)
    chapter_title = ""
    if title_match:
        chapter_title = re.sub(r"<[^>]+>", " ", title_match.group(1))
        chapter_title = re.sub(r"\s+", " ", html_lib.unescape(chapter_title)).strip()

    blocks: list[dict[str, str]] = []
    token_pattern = re.compile(
        r"<(h1|h2|h3|blockquote|li|p|div)[^>]*>(.*?)</\1>",
        flags=re.DOTALL | re.I,
    )
    matches = list(token_pattern.finditer(cleaned))
    if matches:
        for m in matches:
            tag = m.group(1).lower()
            inner = m.group(2)
            # Skip nested container divs that wrap other block elements
            if tag == "div" and re.search(r"<(p|div|h1|h2|h3|blockquote)\b", inner, flags=re.I):
                continue
            inner_with_br = re.sub(r"<br\s*/?>", "\n", inner, flags=re.I)
            plain = re.sub(r"<[^>]+>", "", inner_with_br)
            plain = html_lib.unescape(plain)
            plain = re.sub(r"[ \t]+", " ", plain).strip()
            if not plain:
                continue
            btype = tag if tag in ("h1", "h2", "h3", "blockquote", "li") else "p"
            blocks.append({"type": btype, "text": plain})
    else:
        fallback = clean_html_content(raw_html)
        for para in fallback.splitlines():
            p = para.strip()
            if p:
                blocks.append({"type": "p", "text": p})

    return chapter_title, blocks


def _paginate_blocks(
    blocks: list[dict[str, str]],
    chapter_title: str,
    start_page: int,
    chars_per_page: int = 2200,
) -> list[dict[str, Any]]:
    """Split structured blocks into comfortable book-sized virtual pages without breaking paragraphs."""
    pages: list[dict[str, Any]] = []
    cur_blocks: list[dict[str, str]] = []
    cur_chars = 0
    page_num = start_page

    def flush_page() -> None:
        nonlocal cur_blocks, cur_chars, page_num
        if not cur_blocks:
            return
        plain_text = "\n\n".join(b["text"] for b in cur_blocks)
        pages.append(
            {
                "page": page_num,
                "title": chapter_title,
                "blocks": cur_blocks,
                "text": plain_text,
            }
        )
        page_num += 1
        cur_blocks = []
        cur_chars = 0

    for blk in blocks:
        btext = blk["text"]
        blen = len(btext)
        if blen > chars_per_page * 1.4 and blk["type"] == "p":
            # Split extra-long single paragraph at sentence boundaries
            sentences = re.split(r"(?<=[.!?])\s+", btext)
            buf: list[str] = []
            buf_len = 0
            for s in sentences:
                if buf and buf_len + len(s) > chars_per_page:
                    cur_blocks.append({"type": "p", "text": " ".join(buf)})
                    cur_chars += buf_len
                    flush_page()
                    buf = [s]
                    buf_len = len(s)
                else:
                    buf.append(s)
                    buf_len += len(s) + 1
            if buf:
                btext = " ".join(buf)
                blen = len(btext)
                blk = {"type": "p", "text": btext}
            else:
                continue

        if cur_blocks and (cur_chars + blen > chars_per_page):
            flush_page()
        cur_blocks.append(blk)
        cur_chars += blen

    flush_page()
    return pages


def extract_structured_reader_pages(file_path: str, chars_per_page: int = 2200) -> dict[str, Any]:
    """Extract paginated structured reading pages and TOC for EPUB and TXT documents."""
    if not file_path or not os.path.exists(file_path):
        return {"format": "unknown", "total_pages": 0, "pages": [], "toc": []}

    lower = file_path.lower()
    pages: list[dict[str, Any]] = []
    toc: list[dict[str, Any]] = []

    if lower.endswith(".epub"):
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                opf_path = _locate_opf_path(z)
                entry_paths: list[str] = []
                if opf_path:
                    opf_dir = os.path.dirname(opf_path)
                    opf_data = safe_read_zip_entry(z, opf_path, max_bytes=5 * 1024 * 1024)
                    if opf_data:
                        root_opf = ET.fromstring(opf_data)
                        manifest, spine_idrefs = _parse_opf_manifest_and_spine(root_opf)
                        for idref in spine_idrefs:
                            resolved = _resolve_entry_path(z, opf_dir, manifest[idref])
                            if resolved:
                                entry_paths.append(resolved)

                if not entry_paths:
                    entry_paths = [
                        n
                        for n in sorted(z.namelist())
                        if n.lower().endswith((".html", ".xhtml", ".htm"))
                    ]

                chapter_idx = 0
                for ep in entry_paths:
                    raw_bytes = safe_read_zip_entry(z, ep)
                    if not raw_bytes:
                        continue
                    raw_html = raw_bytes.decode("utf-8", errors="replace")
                    ch_title, blocks = _parse_html_blocks(raw_html)
                    if not blocks:
                        continue
                    chapter_idx += 1
                    label = ch_title or f"Bölüm {chapter_idx}"
                    start_p = len(pages) + 1
                    ch_pages = _paginate_blocks(
                        blocks, label, start_page=start_p, chars_per_page=chars_per_page
                    )
                    if ch_pages:
                        toc.append(
                            {
                                "title": label[:120],
                                "page_number": start_p,
                                "target_page": start_p,
                                "level": 1,
                                "source": "epub_spine",
                            }
                        )
                        pages.extend(ch_pages)
        except Exception as e:
            log_event("epub", "ERROR", f"EPUB okuyucu sayfalandırma hatası ({file_path}): {e}")

        return {
            "format": "epub",
            "total_pages": len(pages),
            "pages": pages,
            "toc": toc,
        }

    # TXT structured pagination (keeping exact 1800-char alignment compatible with chunker where possible)
    raw_txt = extract_text_from_txt(file_path, max_chars=0)
    if not raw_txt or not raw_txt.strip():
        return {"format": "txt", "total_pages": 0, "pages": [], "toc": []}

    heading_re = re.compile(
        r"^(?:bölüm|chapter|part|kısım|\d+\s*[\.\-]|(?:[IVXLCDM]+)\.)\s+.{1,80}$",
        flags=re.I | re.U,
    )
    raw_paras = [p.strip() for p in re.split(r"\r?\n\s*\r?\n", raw_txt) if p.strip()]
    if len(raw_paras) <= 1:
        raw_paras = [ln.strip() for ln in raw_txt.splitlines() if ln.strip()]

    blocks_all: list[dict[str, str]] = []
    for p in raw_paras:
        if len(p) <= 90 and heading_re.match(p):
            blocks_all.append({"type": "h2", "text": p})
        else:
            blocks_all.append({"type": "p", "text": p})

    pages = _paginate_blocks(blocks_all, "", start_page=1, chars_per_page=chars_per_page)
    for pg in pages:
        for blk in pg["blocks"]:
            if blk["type"] in ("h1", "h2"):
                toc.append(
                    {
                        "title": blk["text"][:120],
                        "page_number": pg["page"],
                        "target_page": pg["page"],
                        "level": 1,
                        "source": "txt_heading",
                    }
                )
                if not pg["title"]:
                    pg["title"] = blk["text"][:90]

    return {
        "format": "txt",
        "total_pages": len(pages),
        "pages": pages,
        "toc": toc,
    }
