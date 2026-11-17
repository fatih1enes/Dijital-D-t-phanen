"""app/services/pdf_compressor.py — Local PDF Optimization and Compression Service."""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from collections.abc import Iterator
from typing import Any

import pypdfium2 as pdfium
from PIL import Image

from app.logger import log_event
from app.pdf import PDFIUM_LOCK


class PDFCompressorService:
    """Optimizes heavy scanned PDF documents while protecting selectable vector-text PDFs."""

    @staticmethod
    def _build_metrics(orig_size: int, new_size: int, optimized: bool, message: str = "") -> dict[str, Any]:
        saved_bytes = max(0, orig_size - new_size)
        saved_pct = round((saved_bytes / orig_size) * 100, 1) if orig_size > 0 and optimized else 0.0
        old_mb = round(orig_size / (1024 * 1024), 2)
        new_mb = round(new_size / (1024 * 1024), 2)
        saved_mb = round(saved_bytes / (1024 * 1024), 2)
        res: dict[str, Any] = {
            "success": True,
            "optimized": optimized,
            "original_bytes": orig_size,
            "compressed_bytes": new_size,
            "old_bytes": orig_size,
            "new_bytes": new_size,
            "old_mb": old_mb,
            "new_mb": new_mb,
            "saved_mb": saved_mb,
            "saved_percent": saved_pct,
            "reduction_percent": saved_pct,
        }
        if message:
            res["message"] = message
        return res

    @classmethod
    async def compress_pdf(
        cls,
        file_path: str,
        target_dpi: int = 150,
        quality: int = 76,
    ) -> dict[str, Any]:
        """Compress a scanned/heavy PDF in-place if resulting file is smaller, preserving vector-text PDFs."""
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "Dosya bulunamadı.",
                "message": "Dosya bulunamadı.",
            }

        orig_size = os.path.getsize(file_path)

        def _worker() -> dict[str, Any]:
            tmp_pdf_path: str | None = None
            tmp_page_dir: str | None = None
            try:
                with PDFIUM_LOCK:
                    doc = pdfium.PdfDocument(file_path)
                    try:
                        page_count = len(doc)
                        if page_count == 0:
                            return {
                                "success": False,
                                "error": "Belge boş.",
                                "message": "Belge boş.",
                            }

                        # Inspect sample pages to avoid rasterizing crisp vector-text PDFs
                        sample_count = min(8, page_count)
                        sampled_chars = 0
                        for s_idx in range(sample_count):
                            pg = doc[s_idx]
                            tp = pg.get_textpage()
                            try:
                                sampled_chars += len((tp.get_text_range() or "").strip())
                            finally:
                                tp.close()
                                pg.close()
                    finally:
                        doc.close()

                avg_chars_per_page = sampled_chars / max(1, sample_count)
                avg_bytes_per_page = orig_size / max(1, page_count)
                # Digital text PDFs have rich selectable text and moderate per-page byte footprint
                if avg_chars_per_page >= 220 and avg_bytes_per_page < 320 * 1024:
                    return cls._build_metrics(
                        orig_size,
                        orig_size,
                        optimized=False,
                        message="Bu PDF seçilebilir vektör metin katmanı içeriyor ve zaten kompakt boyutta; metin netliğini bozmamak için orijinal dosya korundu.",
                    )

                tmp_page_dir = tempfile.mkdtemp(prefix="pdf_comp_pages_")
                jpeg_paths: list[str] = []
                scale = target_dpi / 72.0

                # Render one page at a time (releasing PDFIUM_LOCK between pages & keeping RAM flat)
                for p_idx in range(page_count):
                    with PDFIUM_LOCK:
                        doc = pdfium.PdfDocument(file_path)
                        try:
                            page = doc[p_idx]
                            bitmap = page.render(scale=scale)
                            try:
                                pil_img = bitmap.to_pil()
                            finally:
                                bitmap.close()
                                page.close()
                        finally:
                            doc.close()

                    try:
                        if pil_img.mode != "RGB":
                            converted = pil_img.convert("RGB")
                            pil_img.close()
                            pil_img = converted
                        jpg_path = os.path.join(tmp_page_dir, f"p_{p_idx:05d}.jpg")
                        pil_img.save(jpg_path, format="JPEG", quality=quality, optimize=True)
                        jpeg_paths.append(jpg_path)
                    finally:
                        pil_img.close()

                fd, tmp_pdf_path = tempfile.mkstemp(prefix="compressed_", suffix=".pdf")
                os.close(fd)

                def _iter_lazy_images(paths: list[str]) -> Iterator[Image.Image]:
                    for p in paths:
                        with Image.open(p) as im:
                            yield im.copy()

                if jpeg_paths:
                    with Image.open(jpeg_paths[0]) as first_img:
                        first_img.save(
                            tmp_pdf_path,
                            format="PDF",
                            save_all=True,
                            append_images=_iter_lazy_images(jpeg_paths[1:]),
                            resolution=float(target_dpi),
                            quality=quality,
                            optimize=True,
                        )

                new_size = os.path.getsize(tmp_pdf_path)

                if new_size < orig_size and (orig_size - new_size) > 4096:
                    bak_path = file_path + ".bak"
                    shutil.copy2(file_path, bak_path)
                    try:
                        shutil.move(tmp_pdf_path, file_path)
                        if os.path.exists(bak_path):
                            os.remove(bak_path)
                    except Exception as move_err:
                        if os.path.exists(bak_path):
                            shutil.copy2(bak_path, file_path)
                            os.remove(bak_path)
                        raise move_err

                    metrics = cls._build_metrics(orig_size, new_size, optimized=True)
                    log_event(
                        "pdf",
                        "INFO",
                        f"PDF optimize edildi: {os.path.basename(file_path)} ({orig_size // 1024} KB -> {new_size // 1024} KB, %{metrics['saved_percent']} tasarruf)",
                    )
                    return metrics

                if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                    os.remove(tmp_pdf_path)
                return cls._build_metrics(
                    orig_size,
                    orig_size,
                    optimized=False,
                    message="Belge zaten optimum boyutta, orijinal dosya korundu.",
                )
            except Exception as exc:
                log_event("pdf", "ERROR", f"PDF sıkıştırma hatası: {exc}")
                return {"success": False, "error": str(exc), "message": str(exc)}
            finally:
                if tmp_page_dir and os.path.exists(tmp_page_dir):
                    shutil.rmtree(tmp_page_dir, ignore_errors=True)
                if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                    try:
                        os.remove(tmp_pdf_path)
                    except OSError as rm_err:
                        log_event("pdf", "DEBUG", f"Temp pdf cleanup warning: {rm_err}")

        return await asyncio.to_thread(_worker)


pdf_compressor = PDFCompressorService()
