"""Invisible Bounding-Box OCR Layer Service for Scanned (Image-Only) PDFs.

Extracts normalized word-level bounding boxes via pypdfium2 + Tesseract (tur+eng),
caches results per page in SQLite ``kitap_ocr_sayfalar``, and supports full-book
background OCR indexing into ``kitap_chunks`` / ``kitap_chunks_fts``.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from PIL import Image

from app.config import configure_tesseract_from_config, load_config
from app.logger import log_event
from app.pdf import PDFIUM_LOCK


def _render_single_pdf_page_pil(file_path: str, page_num: int) -> Image.Image | None:
    """Render 1-based ``page_num`` to an RGB PIL Image (~180 DPI) for high-accuracy Turkish OCR."""
    if not file_path or not os.path.exists(file_path) or page_num < 1:
        return None

    try:
        import pypdfium2

        with PDFIUM_LOCK:
            doc = pypdfium2.PdfDocument(file_path)
            try:
                total = len(doc)
                if page_num > total:
                    return None
                page = doc[page_num - 1]
                bitmap = page.render(scale=2.5)
                try:
                    pil_img = bitmap.to_pil()
                finally:
                    bitmap.close()
                    page.close()
                if pil_img.mode != "RGB":
                    rgb_img = pil_img.convert("RGB")
                    pil_img.close()
                    return rgb_img
                return pil_img
            finally:
                doc.close()
    except Exception as fast_err:
        log_event("pdf", "DEBUG", f"OCR pypdfium2 sayfa {page_num} yedeklemeye geçiyor: {fast_err}")

    try:
        import pdf2image

        imgs = pdf2image.convert_from_path(
            file_path, first_page=page_num, last_page=page_num, dpi=180
        )
        if imgs:
            first = imgs[0]
            for extra in imgs[1:]:
                extra.close()
            if first.mode != "RGB":
                rgb = first.convert("RGB")
                first.close()
                return rgb
            return first
    except Exception as fb_err:
        log_event("pdf", "WARNING", f"OCR sayfa {page_num} görüntü oluşturma hatası: {fb_err}")
    return None


def extract_page_ocr_boxes_sync(file_path: str, page_num: int) -> dict[str, Any]:
    """Run Tesseract word-box OCR on a single PDF page synchronously on a worker thread."""
    cfg = load_config()
    configure_tesseract_from_config(cfg)

    pil_img = _render_single_pdf_page_pil(file_path, page_num)
    if pil_img is None:
        return {
            "available": False,
            "img_w": 0,
            "img_h": 0,
            "words": [],
            "full_text": "",
            "reason": "page_render_failed",
        }

    try:
        import pytesseract

        img_w, img_h = pil_img.size
        if img_w <= 0 or img_h <= 0:
            return {
                "available": False,
                "img_w": 0,
                "img_h": 0,
                "words": [],
                "full_text": "",
                "reason": "invalid_dimensions",
            }

        try:
            data = pytesseract.image_to_data(
                pil_img,
                lang="tur+eng",
                config="--psm 1",
                output_type=pytesseract.Output.DICT,
            )
        except pytesseract.TesseractError:
            data = pytesseract.image_to_data(
                pil_img,
                lang="eng",
                config="--psm 1",
                output_type=pytesseract.Output.DICT,
            )

        texts = data.get("text") or []
        confs = data.get("conf") or []
        lefts = data.get("left") or []
        tops = data.get("top") or []
        widths = data.get("width") or []
        heights = data.get("height") or []
        blocks = data.get("block_num") or []
        pars = data.get("par_num") or []
        lines = data.get("line_num") or []

        words: list[dict[str, Any]] = []
        grouped_lines: dict[tuple[int, int, int], list[str]] = {}

        count = len(texts)
        for i in range(count):
            raw_word = str(texts[i] or "").strip()
            if not raw_word:
                continue
            try:
                conf_val = float(confs[i])
            except (TypeError, ValueError):
                conf_val = 0.0
            if conf_val < 12.0:
                continue

            lx = max(0, int(lefts[i] or 0))
            ty = max(0, int(tops[i] or 0))
            bw = max(1, int(widths[i] or 1))
            bh = max(1, int(heights[i] or 1))
            b_no = int(blocks[i] or 0) if i < len(blocks) else 0
            p_no = int(pars[i] or 0) if i < len(pars) else 0
            l_no = int(lines[i] or 0) if i < len(lines) else 0

            words.append(
                {
                    "t": raw_word,
                    "x": round(min(1.0, lx / img_w), 5),
                    "y": round(min(1.0, ty / img_h), 5),
                    "w": round(min(1.0, bw / img_w), 5),
                    "h": round(min(1.0, bh / img_h), 5),
                    "b": b_no,
                    "l": l_no,
                }
            )
            grouped_lines.setdefault((b_no, p_no, l_no), []).append(raw_word)

        ordered_lines: list[str] = []
        prev_bp: tuple[int, int] | None = None
        for key in sorted(grouped_lines.keys()):
            bp = (key[0], key[1])
            line_str = " ".join(grouped_lines[key]).strip()
            if not line_str:
                continue
            if prev_bp is not None and bp != prev_bp:
                ordered_lines.append("")
            ordered_lines.append(line_str)
            prev_bp = bp

        full_text = "\n".join(ordered_lines).strip()
        return {
            "available": True,
            "img_w": int(img_w),
            "img_h": int(img_h),
            "words": words,
            "full_text": full_text,
        }
    except Exception as ocr_err:
        log_event("pdf", "WARNING", f"Tesseract kelime katmanı OCR uyarısı (s.{page_num}): {ocr_err}")
        return {
            "available": False,
            "img_w": 0,
            "img_h": 0,
            "words": [],
            "full_text": "",
            "reason": str(ocr_err),
        }
    finally:
        try:
            pil_img.close()
        except Exception as cl_err:
            log_event("pdf", "DEBUG", f"OCR PIL close note: {cl_err}")


class OcrLayerService:
    """Manages SQLite caching and on-demand/background OCR word-box extraction."""

    async def get_or_extract_page_ocr(
        self,
        db: Any,
        file_hash: str,
        file_path: str,
        page_num: int,
    ) -> dict[str, Any]:
        """Return cached OCR word boxes for ``(file_hash, page_num)`` or compute and cache them."""
        conn = getattr(db, "conn", db)
        try:
            cur = await conn.execute(
                """
                SELECT img_w, img_h, words_json, full_text
                FROM kitap_ocr_sayfalar
                WHERE dosya_hash = ? AND sayfa_no = ?
                """,
                (file_hash, page_num),
            )
            row = await cur.fetchone()
            if row is not None:
                words_parsed = json.loads(row[2] or "[]")
                return {
                    "file_hash": file_hash,
                    "page": page_num,
                    "cached": True,
                    "available": True,
                    "img_w": int(row[0] or 0),
                    "img_h": int(row[1] or 0),
                    "words": words_parsed,
                    "full_text": str(row[3] or ""),
                }
        except Exception as cache_err:
            log_event("database", "DEBUG", f"OCR önbellek okuma notu: {cache_err}")

        extracted = await asyncio.to_thread(extract_page_ocr_boxes_sync, file_path, page_num)
        if extracted.get("available"):
            try:
                await conn.execute(
                    """
                    INSERT INTO kitap_ocr_sayfalar (dosya_hash, sayfa_no, img_w, img_h, words_json, full_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(dosya_hash, sayfa_no) DO UPDATE SET
                        img_w = excluded.img_w,
                        img_h = excluded.img_h,
                        words_json = excluded.words_json,
                        full_text = excluded.full_text
                    """,
                    (
                        file_hash,
                        page_num,
                        int(extracted.get("img_w") or 0),
                        int(extracted.get("img_h") or 0),
                        json.dumps(extracted.get("words") or [], ensure_ascii=False),
                        str(extracted.get("full_text") or ""),
                    ),
                )
                await conn.commit()
            except Exception as save_err:
                log_event("database", "DEBUG", f"OCR önbellek yazma notu: {save_err}")

        return {
            "file_hash": file_hash,
            "page": page_num,
            "cached": False,
            **extracted,
        }


ocr_layer_service = OcrLayerService()
