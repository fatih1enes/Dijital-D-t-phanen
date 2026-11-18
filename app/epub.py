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


def _extract_footnotes_from_html(raw_html: str) -> dict[str, str]:
    """Extract footnote/endnote definitions keyed by element id from EPUB XHTML."""
    notes: dict[str, str] = {}
    if not raw_html:
        return notes

    fn_pattern = re.compile(
        r'<(aside|li|div|p)\b([^>]*\bid=["\']([^"\']+)["\'][^>]*)>(.*?)</\1>',
        flags=re.DOTALL | re.I,
    )
    for m in fn_pattern.finditer(raw_html):
        tag_name = m.group(1).lower()
        attrs = m.group(2)
        fn_id = m.group(3).strip()
        inner = m.group(4)
        is_explicit_fn = (
            "noteref" not in attrs.lower()
            and (
                "footnote" in attrs.lower()
                or "endnote" in attrs.lower()
                or "rearnote" in attrs.lower()
                or fn_id.lower().startswith(("fn", "note", "dipnot", "en"))
                or tag_name == "aside"
            )
        )
        if not is_explicit_fn:
            continue
        txt = re.sub(r"<[^>]+>", " ", inner)
        txt = re.sub(r"\s+", " ", html.unescape(txt)).strip()
        # Strip leading backlink arrows like ↑ or ↩
        txt = re.sub(r"^[\[\(]?\d+[\]\)\.]?\s*", "", txt).rstrip("↩↑ ").strip()
        if txt and len(txt) <= 1500:
            notes[fn_id] = txt
    return notes


def _parse_html_blocks(
    raw_html: str,
    z: zipfile.ZipFile | None = None,
    entry_dir: str = "",
    known_footnotes: dict[str, str] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Extract chapter heading and rich structured blocks (headings, quotes, lists, images, footnotes) from EPUB XHTML."""
    import html as html_lib

    if not raw_html:
        return "", []

    cleaned = re.sub(r"<(script|style|head)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.I)
    # Remove explicit <aside epub:type="footnote"> blocks from main body flow so footnotes don't duplicate inline
    cleaned_body = re.sub(
        r"<aside\b[^>]*(?:footnote|endnote|rearnote)[^>]*>.*?</aside>",
        "",
        cleaned,
        flags=re.DOTALL | re.I,
    )

    title_match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", cleaned_body, flags=re.DOTALL | re.I)
    chapter_title = ""
    if title_match:
        chapter_title = re.sub(r"<[^>]+>", " ", title_match.group(1))
        chapter_title = re.sub(r"\s+", " ", html_lib.unescape(chapter_title)).strip()

    blocks: list[dict[str, Any]] = []
    fn_lookup = known_footnotes or {}

    token_pattern = re.compile(
        r"<(h1|h2|h3|blockquote|li|p|div)\b([^>]*)>(.*?)</\1>|<img\b([^>]*)/?>|<image\b([^>]*)/?>",
        flags=re.DOTALL | re.I,
    )
    matches = list(token_pattern.finditer(cleaned_body))
    if matches:
        for m in matches:
            img_attrs = m.group(4) or m.group(5)
            if img_attrs is not None:
                src_m = re.search(
                    r'(?:src|xlink:href|href)=["\']([^"\']+)["\']', img_attrs, flags=re.I
                )
                alt_m = re.search(r'alt=["\']([^"\']*)["\']', img_attrs, flags=re.I)
                raw_src = src_m.group(1).strip() if src_m else ""
                alt_txt = html_lib.unescape(alt_m.group(1)).strip() if alt_m else ""
                if raw_src and z is not None:
                    clean_href = raw_src.split("#", 1)[0].split("?", 1)[0]
                    resolved_img = _resolve_entry_path(z, entry_dir, clean_href)
                    if resolved_img:
                        blocks.append(
                            {
                                "type": "image",
                                "tag": "img",
                                "src": resolved_img,
                                "alt": alt_txt,
                                "text": alt_txt,
                            }
                        )
                continue

            tag = m.group(1).lower()
            block_attrs = m.group(2) or ""
            inner = m.group(3) or ""

            # Skip standalone footnote definition list items at bottom if already captured in footnote popover map
            id_m = re.search(r'\bid=["\']([^"\']+)["\']', block_attrs, flags=re.I)
            if id_m and id_m.group(1) in fn_lookup and (
                "footnote" in block_attrs.lower() or tag == "li"
            ):
                continue

            if tag == "div" and re.search(
                r"<(p|div|h1|h2|h3|blockquote|img|image)\b", inner, flags=re.I
            ):
                continue

            # Check for embedded <img> inside <p> or <div>
            if z is not None:
                for inline_img in re.finditer(r"<img\b([^>]*)/?>", inner, flags=re.I):
                    ia = inline_img.group(1)
                    sm = re.search(r'src=["\']([^"\']+)["\']', ia, flags=re.I)
                    am = re.search(r'alt=["\']([^"\']*)["\']', ia, flags=re.I)
                    if sm:
                        chref = sm.group(1).split("#", 1)[0].split("?", 1)[0]
                        r_img = _resolve_entry_path(z, entry_dir, chref)
                        if r_img:
                            alt_s = html_lib.unescape(am.group(1)).strip() if am else ""
                            blocks.append(
                                {
                                    "type": "image",
                                    "tag": "img",
                                    "src": r_img,
                                    "alt": alt_s,
                                    "text": alt_s,
                                }
                            )

            # Extract inline footnote references (<a href="#fn1">1</a>) and strip raw anchor text to prevent "1 [1]" duplication
            block_footnotes: list[dict[str, str]] = []
            cleaned_inner_parts: list[str] = []
            last_idx = 0
            for a_m in re.finditer(
                r'<a\b([^>]*href=["\']([^"\']*#([^"\']+))["\'][^>]*)>(.*?)</a>',
                inner,
                flags=re.DOTALL | re.I,
            ):
                a_attrs = a_m.group(1).lower()
                frag_id = a_m.group(3).strip()
                label_raw = re.sub(r"<[^>]+>", "", a_m.group(4)).strip()
                clean_lbl = re.sub(r"^[(\[.]?\s*|\s*[)\].]?$", "", label_raw) or "*"
                if frag_id in fn_lookup or "noteref" in a_attrs or re.match(
                    r"^\[?\d+\.?\]?$", label_raw
                ):
                    fn_body = fn_lookup.get(frag_id, "")
                    if fn_body:
                        block_footnotes.append(
                            {
                                "id": frag_id,
                                "label": clean_lbl,
                                "content": fn_body,
                            }
                        )
                        cleaned_inner_parts.append(inner[last_idx : a_m.start()])
                        last_idx = a_m.end()
                        continue
                cleaned_inner_parts.append(inner[last_idx : a_m.end()])
                last_idx = a_m.end()
            cleaned_inner_parts.append(inner[last_idx:])
            inner_no_fn = "".join(cleaned_inner_parts)

            inner_with_br = re.sub(r"<br\s*/?>", "\n", inner_no_fn, flags=re.I)
            plain = re.sub(r"<[^>]+>", "", inner_with_br)
            plain = html_lib.unescape(plain)
            plain = re.sub(r"[ \t]+", " ", plain).strip()
            if not plain:
                continue
            btype = tag if tag in ("h1", "h2", "h3", "blockquote", "li") else "p"
            blk_obj: dict[str, Any] = {"type": btype, "tag": btype, "text": plain}
            if block_footnotes:
                blk_obj["footnotes"] = block_footnotes
            blocks.append(blk_obj)
    else:
        fallback = clean_html_content(raw_html)
        for para in fallback.splitlines():
            p = para.strip()
            if p:
                blocks.append({"type": "p", "tag": "p", "text": p})

    return chapter_title, blocks


def _parse_epub_rich_toc(
    z: zipfile.ZipFile,
    root_opf: Any,
    opf_dir: str,
    entry_start_page: dict[str, int],
) -> list[dict[str, Any]]:
    """Parse hierarchical TOC from EPUB3 <nav> or EPUB2 toc.ncx and map entries to virtual pages."""
    toc_items: list[dict[str, Any]] = []

    def _resolve_target_page(raw_href: str, nav_dir: str) -> int:
        clean_part = raw_href.split("#", 1)[0].split("?", 1)[0].strip()
        if not clean_part:
            return 1
        resolved = _resolve_entry_path(z, nav_dir, clean_part)
        if resolved and resolved in entry_start_page:
            return entry_start_page[resolved]
        for k, p_no in entry_start_page.items():
            if k.endswith(clean_part) or os.path.basename(k) == os.path.basename(clean_part):
                return p_no
        return 1

    # 1. Try EPUB3 <item properties="nav">
    nav_href = None
    ncx_href = None
    for item in root_opf.findall(".//{http://www.idpf.org/2007/opf}item"):
        props = (item.attrib.get("properties") or "").split()
        mtype = (item.attrib.get("media-type") or "").lower()
        href = item.attrib.get("href") or ""
        if "nav" in props and href:
            nav_href = href
        elif ("ncx" in mtype or href.lower().endswith(".ncx")) and href:
            ncx_href = href

    if nav_href:
        nav_entry = _resolve_entry_path(z, opf_dir, nav_href)
        if nav_entry:
            raw_nav = safe_read_zip_entry(z, nav_entry, max_bytes=4 * 1024 * 1024)
            if raw_nav:
                try:
                    nav_root = ET.fromstring(raw_nav)
                    nav_dir = os.path.dirname(nav_entry)
                    target_nav = None
                    for nav_el in nav_root.findall(".//*"):
                        if nav_el.tag.endswith("nav"):
                            etype = " ".join(
                                str(v) for k, v in nav_el.attrib.items() if k.endswith("type")
                            )
                            if "toc" in etype.lower() or target_nav is None:
                                target_nav = nav_el
                                if "toc" in etype.lower():
                                    break

                    def _walk_nav_ol(ol_el: Any, level: int) -> None:
                        for child in list(ol_el):
                            if not child.tag.endswith("li"):
                                continue
                            link_el = None
                            sub_ol = None
                            for sub in list(child):
                                if sub.tag.endswith("a") and link_el is None:
                                    link_el = sub
                                elif sub.tag.endswith("ol") and sub_ol is None:
                                    sub_ol = sub
                            if link_el is not None:
                                lbl = "".join(link_el.itertext()).strip()
                                lbl = re.sub(r"\s+", " ", lbl)
                                href_v = link_el.attrib.get("href") or ""
                                if lbl:
                                    pg_no = _resolve_target_page(href_v, nav_dir)
                                    toc_items.append(
                                        {
                                            "title": lbl[:140],
                                            "page_number": pg_no,
                                            "target_page": pg_no,
                                            "level": min(3, max(1, level)),
                                            "source": "epub_nav",
                                        }
                                    )
                            if sub_ol is not None:
                                _walk_nav_ol(sub_ol, level + 1)

                    if target_nav is not None:
                        for child_ol in list(target_nav):
                            if child_ol.tag.endswith("ol"):
                                _walk_nav_ol(child_ol, 1)
                    if toc_items:
                        return toc_items
                except Exception as nav_err:
                    log_event("epub", "DEBUG", f"EPUB3 nav ayrıştırma notu: {nav_err}")

    # 2. Try EPUB2 toc.ncx
    if ncx_href:
        ncx_entry = _resolve_entry_path(z, opf_dir, ncx_href)
        if ncx_entry:
            raw_ncx = safe_read_zip_entry(z, ncx_entry, max_bytes=4 * 1024 * 1024)
            if raw_ncx:
                try:
                    ncx_root = ET.fromstring(raw_ncx)
                    ncx_dir = os.path.dirname(ncx_entry)

                    def _walk_navpoints(parent_el: Any, level: int) -> None:
                        for np_el in list(parent_el):
                            if not np_el.tag.endswith("navPoint"):
                                continue
                            lbl = ""
                            src_v = ""
                            for sub in np_el.iter():
                                if sub.tag.endswith("text") and not lbl and sub.text:
                                    lbl = re.sub(r"\s+", " ", sub.text).strip()
                                elif sub.tag.endswith("content") and not src_v:
                                    src_v = sub.attrib.get("src") or ""
                            if lbl:
                                pg_no = _resolve_target_page(src_v, ncx_dir)
                                toc_items.append(
                                    {
                                        "title": lbl[:140],
                                        "page_number": pg_no,
                                        "target_page": pg_no,
                                        "level": min(3, max(1, level)),
                                        "source": "epub_ncx",
                                    }
                                )
                            _walk_navpoints(np_el, level + 1)

                    for nm in ncx_root.iter():
                        if nm.tag.endswith("navMap"):
                            _walk_navpoints(nm, 1)
                            break
                except Exception as ncx_err:
                    log_event("epub", "DEBUG", f"EPUB2 ncx ayrıştırma notu: {ncx_err}")

    return toc_items


def _paginate_blocks(
    blocks: list[dict[str, Any]],
    chapter_title: str,
    start_page: int,
    chars_per_page: int = 2200,
) -> list[dict[str, Any]]:
    """Split structured blocks into comfortable book-sized virtual pages without breaking paragraphs."""
    pages: list[dict[str, Any]] = []
    cur_blocks: list[dict[str, Any]] = []
    cur_chars = 0
    page_num = start_page

    def flush_page() -> None:
        nonlocal cur_blocks, cur_chars, page_num
        if not cur_blocks:
            return
        plain_text = "\n\n".join(str(b.get("text") or "") for b in cur_blocks if b.get("text"))
        pages.append(
            {
                "page": page_num,
                "page_num": page_num,
                "title": chapter_title,
                "blocks": cur_blocks,
                "text": plain_text,
            }
        )
        page_num += 1
        cur_blocks = []
        cur_chars = 0

    for blk in blocks:
        btype = str(blk.get("type") or "p")
        btext = str(blk.get("text") or "")
        blen = 350 if btype == "image" else len(btext)
        if blen > chars_per_page * 1.4 and btype == "p":
            sentences = re.split(r"(?<=[.!?])\s+", btext)
            buf: list[str] = []
            buf_len = 0
            for s in sentences:
                if buf and buf_len + len(s) > chars_per_page:
                    cur_blocks.append({"type": "p", "tag": "p", "text": " ".join(buf)})
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
                new_blk: dict[str, Any] = {"type": "p", "tag": "p", "text": btext}
                if blk.get("footnotes"):
                    new_blk["footnotes"] = blk["footnotes"]
                blk = new_blk
            else:
                continue

        if cur_blocks and (cur_chars + blen > chars_per_page):
            flush_page()
        cur_blocks.append(blk)
        cur_chars += blen

    flush_page()
    return pages


def extract_structured_reader_pages(file_path: str, chars_per_page: int = 2200) -> dict[str, Any]:
    """Extract paginated structured reading pages, rich TOC, images, and footnotes for EPUB and TXT."""
    if not file_path or not os.path.exists(file_path):
        return {"format": "unknown", "total_pages": 0, "pages": [], "toc": [], "footnotes": {}}

    lower = file_path.lower()
    pages: list[dict[str, Any]] = []
    toc: list[dict[str, Any]] = []
    all_footnotes: dict[str, str] = {}

    if lower.endswith(".epub"):
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                opf_path = _locate_opf_path(z)
                opf_dir = os.path.dirname(opf_path) if opf_path else ""
                root_opf: Any = None
                entry_paths: list[str] = []
                if opf_path:
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

                # Pass 1: collect all footnote/endnote definitions across spine files
                decoded_entries: list[tuple[str, str]] = []
                for ep in entry_paths:
                    raw_bytes = safe_read_zip_entry(z, ep)
                    if not raw_bytes:
                        continue
                    raw_html = _decode_epub_bytes(raw_bytes)
                    decoded_entries.append((ep, raw_html))
                    all_footnotes.update(_extract_footnotes_from_html(raw_html))

                # Pass 2: build paginated structured blocks and track start_page per spine file
                spine_toc: list[dict[str, Any]] = []
                entry_start_page: dict[str, int] = {}
                chapter_idx = 0
                for ep, raw_html in decoded_entries:
                    ep_dir = os.path.dirname(ep)
                    ch_title, blocks = _parse_html_blocks(
                        raw_html,
                        z=z,
                        entry_dir=ep_dir,
                        known_footnotes=all_footnotes,
                    )
                    if not blocks:
                        continue
                    chapter_idx += 1
                    label = ch_title or f"Bölüm {chapter_idx}"
                    start_p = len(pages) + 1
                    entry_start_page[ep] = start_p
                    ch_pages = _paginate_blocks(
                        blocks, label, start_page=start_p, chars_per_page=chars_per_page
                    )
                    if ch_pages:
                        spine_toc.append(
                            {
                                "title": label[:120],
                                "page_number": start_p,
                                "target_page": start_p,
                                "level": 1,
                                "source": "epub_spine",
                            }
                        )
                        pages.extend(ch_pages)

                if root_opf is not None and entry_start_page:
                    rich_toc = _parse_epub_rich_toc(z, root_opf, opf_dir, entry_start_page)
                    toc = rich_toc if rich_toc else spine_toc
                else:
                    toc = spine_toc
        except Exception as e:
            log_event("epub", "ERROR", f"EPUB okuyucu sayfalandırma hatası ({file_path}): {e}")

        return {
            "format": "epub",
            "total_pages": len(pages),
            "pages": pages,
            "toc": toc,
            "footnotes": all_footnotes,
        }

    # TXT structured pagination
    raw_txt = extract_text_from_txt(file_path, max_chars=0)
    if not raw_txt or not raw_txt.strip():
        return {"format": "txt", "total_pages": 0, "pages": [], "toc": [], "footnotes": {}}

    heading_re = re.compile(
        r"^(?:bölüm|chapter|part|kısım|\d+\s*[\.\-]|(?:[IVXLCDM]+)\.)\s+.{1,80}$",
        flags=re.I | re.U,
    )
    raw_paras = [p.strip() for p in re.split(r"\r?\n\s*\r?\n", raw_txt) if p.strip()]
    if len(raw_paras) <= 1:
        raw_paras = [ln.strip() for ln in raw_txt.splitlines() if ln.strip()]

    blocks_all: list[dict[str, Any]] = []
    for p in raw_paras:
        if len(p) <= 90 and heading_re.match(p):
            blocks_all.append({"type": "h2", "tag": "h2", "text": p})
        else:
            blocks_all.append({"type": "p", "tag": "p", "text": p})

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
        "footnotes": {},
    }
