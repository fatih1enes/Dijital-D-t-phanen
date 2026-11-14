"""PDF Table of Contents (TOC) extraction and automatic offset solver service."""

import asyncio
import os
import re
from collections import Counter
from typing import Any

from app.database import DatabaseManager
from app.logger import log_event
from app.pdf import PDFIUM_LOCK


def _clean_toc_title(title: str) -> str:
    """Normalize OCR artifacts, Turkish character anomalies, and Roman numerals in TOC titles."""
    if not title:
        return ""
    t = title.strip()
    # Normalize Roman numerals at line start: e.g. 'ı.' -> 'I. ', 'ıı.' -> 'II. '
    t = re.sub(r"^[ıi]\.\s*", "I. ", t)
    t = re.sub(r"^[ıi][ıi]\.\s*", "II. ", t)
    t = re.sub(r"^[ıi][ıi][ıi]\.\s*", "III. ", t)
    t = re.sub(r"^[ıi]v\.\s*", "IV. ", t, flags=re.I)
    t = re.sub(r"^v[ıi]\.\s*", "VI. ", t, flags=re.I)
    t = re.sub(r"^v[ıi][ıi]\.\s*", "VII. ", t, flags=re.I)
    t = re.sub(r"^v[ıi][ıi][ıi]\.\s*", "VIII. ", t, flags=re.I)
    t = re.sub(r"^[ıi]x\.\s*", "IX. ", t, flags=re.I)
    t = re.sub(r"^x\.\s*", "X. ", t, flags=re.I)

    # Fix digit '1' embedded within words as 'i' or 'I' (e.g., NED1R -> NEDİR, KlAS1K -> KLASİK)
    t = re.sub(r"([A-Za-zğüşöçıİĞÜŞÖÇ])1([A-Za-zğüşöçıİĞÜŞÖÇ])", r"\g<1>i\g<2>", t)
    t = re.sub(r"1([A-Za-zğüşöçıİĞÜŞÖÇ])", r"İ\1", t)

    # Fix common Turkish Tasavvuf OCR glitches: 'TASAWUF' -> 'TASAVVUF'
    t = re.sub(r"TASAW[Uu]F", "TASAVVUF", t)
    t = re.sub(r"tasaw[u]f", "tasavvuf", t)

    # Fix leading lowercase 'l' recognized instead of capital 'İ' or 'I'
    t = re.sub(r"\blNSAN\b", "İNSAN", t)
    t = re.sub(r"\blbadet", "İbadet", t)

    return t.strip()


class TOCService:
    """Extracts native PDF bookmarks or synthesizes TOC and solves page number offsets."""

    @classmethod
    async def get_or_generate_toc(
        cls,
        db: DatabaseManager,
        file_hash: str,
    ) -> list[dict[str, Any]]:
        """Retrieve stored TOC or automatically extract/synthesize from the document."""
        # 1. Check existing records in database
        cur = await db.conn.execute(
            """
            SELECT id, title, page_number, target_page, level, source
            FROM kitap_toc
            WHERE dosya_hash = ?
            ORDER BY target_page ASC, page_number ASC, id ASC
            """,
            (file_hash,),
        )
        rows = await cur.fetchall()
        if rows:
            return [
                {
                    "id": r[0],
                    "title": r[1],
                    "page_number": r[2],
                    "target_page": r[3],
                    "level": r[4],
                    "source": r[5],
                }
                for r in rows
            ]

        # 2. Get file path
        path_info = await db.get_book_path(file_hash)
        if not path_info or not path_info[0]:
            return []

        file_path = path_info[0]
        if not os.path.exists(file_path) or not file_path.lower().endswith(".pdf"):
            return []

        # 3. Try native outline via pypdfium2
        native_items = await asyncio.to_thread(cls._extract_native_outline, file_path)
        if native_items:
            await cls._save_toc_items(db, file_hash, native_items)
            return native_items

        # 4. Synthesize TOC and solve page offset if native outline is missing
        auto_items = await asyncio.to_thread(cls._synthesize_toc_from_text, file_path)
        if auto_items:
            await cls._save_toc_items(db, file_hash, auto_items)
            return auto_items

        return []

    @classmethod
    def _extract_native_outline(cls, file_path: str) -> list[dict[str, Any]]:
        """Extract bookmarks/outline using pypdfium2 with thread synchronization."""
        items: list[dict[str, Any]] = []
        doc = None
        try:
            import pypdfium2 as pdfium

            with PDFIUM_LOCK:
                doc = pdfium.PdfDocument(file_path)
                raw_toc = list(doc.get_toc())
                for node in raw_toc:
                    title = _clean_toc_title(str(getattr(node, "title", "") or "").strip())
                    page_idx = getattr(node, "page_index", None)
                    level = getattr(node, "level", 1) or 1
                    if title and page_idx is not None and page_idx >= 0:
                        page_num = page_idx + 1
                        items.append(
                            {
                                "title": title,
                                "page_number": page_num,
                                "target_page": page_num,
                                "level": min(3, max(1, level)),
                                "source": "native",
                            }
                        )
        except Exception as e:
            log_event("pdf", "DEBUG", f"Native PDF outline okuma uyarısı: {e}")
        finally:
            if doc is not None:
                try:
                    with PDFIUM_LOCK:
                        doc.close()
                except Exception as close_err:
                    log_event("pdf", "DEBUG", f"Native outline doc close error: {close_err}")
        return items

    @classmethod
    def _synthesize_toc_from_text(cls, file_path: str) -> list[dict[str, Any]]:
        """Scan front matter pages for TOC tables, extract entries and calculate page offset with voting."""
        items: list[dict[str, Any]] = []
        doc = None
        try:
            import pypdfium2 as pdfium

            with PDFIUM_LOCK:
                doc = pdfium.PdfDocument(file_path)
                total_pages = len(doc)
                scan_pages = min(30, total_pages)

                toc_header_regex = re.compile(
                    r"(?:içindekiler|contents|table\s+of\s+contents|fihrist)",
                    re.IGNORECASE | re.UNICODE,
                )
                dotted_line_regex = re.compile(
                    r"^(.{2,90}?)\s*[\.\s\-_–—…]{2,}\s*(\d{1,4})$",
                    re.UNICODE,
                )
                simple_toc_regex = re.compile(
                    r"^((?:bölüm|chapter|part|\d+\.|\b[ivxlcdm]+\.)\s*.{2,80}?)\s+(\d{1,4})$",
                    re.IGNORECASE | re.UNICODE,
                )

                detected_entries: list[
                    tuple[str, int, int]
                ] = []  # (title, stated_page, found_on_pdf_page)
                in_toc_section = False

                for p_idx in range(scan_pages):
                    page = doc.get_page(p_idx)
                    textpage = page.get_textpage()
                    raw_text = textpage.get_text_range()
                    if not raw_text:
                        continue

                    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

                    for line in lines:
                        if toc_header_regex.search(line):
                            in_toc_section = True
                            continue

                        if in_toc_section:
                            # Check dotted pattern: e.g. "Giriş ................... 12"
                            m1 = dotted_line_regex.match(line)
                            if m1:
                                t = _clean_toc_title(m1.group(1).strip())
                                p = int(m1.group(2))
                                if t and 0 < p < total_pages * 2:
                                    detected_entries.append((t, p, p_idx + 1))
                                continue

                            # Check simple pattern: e.g. "Bölüm 1 Temel Kavramlar 15"
                            m2 = simple_toc_regex.match(line)
                            if m2:
                                t = _clean_toc_title(m2.group(1).strip())
                                p = int(m2.group(2))
                                if t and 0 < p < total_pages * 2:
                                    detected_entries.append((t, p, p_idx + 1))
                                continue

                if not detected_entries:
                    return []

                # 4. Multi-candidate offset voting solver:
                # Tests multiple chapter titles against actual page text around stated page numbers
                offset_votes: Counter = Counter()

                for entry in detected_entries:
                    raw_title, stated_page, _ = entry
                    # Skip illustrations, tables, or very short front matter
                    if stated_page <= 0:
                        continue
                    clean_t = re.sub(r"^(?:[IVXLCDM]+|\d+)[\.\-\:\s]\s*", "", raw_title, flags=re.IGNORECASE)
                    kw_tokens = [w for w in re.split(r"\W+", clean_t) if len(w) >= 4]
                    if not kw_tokens:
                        continue

                    # Search within stated_page - 4 to stated_page + 30
                    search_start = max(0, stated_page - 4)
                    search_end = min(total_pages, stated_page + 30)
                    kw_normalized = [
                        k.lower().replace("1", "i").replace("w", "v") for k in kw_tokens[:2]
                    ]

                    for check_idx in range(search_start, search_end):
                        p = doc.get_page(check_idx)
                        tp = p.get_textpage()
                        try:
                            p_text = (tp.get_text_range() or "").lower()
                            p_text = p_text.replace("1", "i").replace("w", "v")
                            if all(tok in p_text for tok in kw_normalized):
                                actual_pdf_page = check_idx + 1
                                cand_offset = actual_pdf_page - stated_page
                                offset_votes[cand_offset] += 1
                                break
                        finally:
                            tp.close()
                            p.close()

                # Pick offset with highest consensus, defaulting to 0
                offset = 0
                if offset_votes:
                    most_common_offset, count = offset_votes.most_common(1)[0]
                    if count >= 1:
                        offset = most_common_offset

                # Build final items
                for title, stated_page, _ in detected_entries:
                    target_page = max(1, min(total_pages, stated_page + offset))
                    items.append(
                        {
                            "title": title,
                            "page_number": stated_page,
                            "target_page": target_page,
                            "level": 1,
                            "source": "auto_detected",
                        }
                    )

        except Exception as e:
            log_event("pdf", "WARNING", f"TOC sentezleme uyarısı: {e}")
        finally:
            if doc is not None:
                try:
                    with PDFIUM_LOCK:
                        doc.close()
                except Exception as close_err:
                    log_event("pdf", "DEBUG", f"TOC doc close error: {close_err}")

        return items

    @classmethod
    async def _save_toc_items(
        cls,
        db: DatabaseManager,
        file_hash: str,
        items: list[dict[str, Any]],
    ) -> None:
        """Persist TOC items to the database."""
        try:
            # Clear previous partial/erroneous entries for this book
            await db.conn.execute("DELETE FROM kitap_toc WHERE dosya_hash = ?", (file_hash,))
            for it in items:
                await db.conn.execute(
                    """
                    INSERT INTO kitap_toc (dosya_hash, title, page_number, target_page, level, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_hash,
                        it["title"],
                        it["page_number"],
                        it["target_page"],
                        it.get("level", 1),
                        it.get("source", "native"),
                    ),
                )
            await db.conn.commit()
        except Exception as e:
            log_event("database", "WARNING", f"TOC kayıt hatası: {e}")


toc_service = TOCService()
