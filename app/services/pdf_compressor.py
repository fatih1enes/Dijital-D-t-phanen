"""app/services/pdf_compressor.py — Local PDF Optimization and Compression Service."""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from typing import Any

import pypdfium2 as pdfium
from PIL import Image

from app.logger import log_event
from app.pdf import PDFIUM_LOCK


class PDFCompressorService:
    """Optimizes heavy and scanned PDF documents using localized multi-scale image recompression."""

    @staticmethod
    async def compress_pdf(
        file_path: str,
        target_dpi: int = 150,
        quality: int = 76,
    ) -> dict[str, Any]:
        """Compress a PDF file in-place if resulting file is smaller."""
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "Dosya bulunamadı.",
                "message": "Dosya bulunamadı.",
            }

        orig_size = os.path.getsize(file_path)

        def _worker() -> dict[str, Any]:
            doc: pdfium.PdfDocument | None = None
            tmp_pdf_path: str | None = None
            images: list[Image.Image] = []
            try:
                with PDFIUM_LOCK:
                    doc = pdfium.PdfDocument(file_path)
                    page_count = len(doc)
                    if page_count == 0:
                        doc.close()
                        return {
                            "success": False,
                            "error": "Belge boş.",
                            "message": "Belge boş.",
                        }

                    for p_idx in range(page_count):
                        page = doc[p_idx]
                        scale = target_dpi / 72.0
                        bitmap = page.render(scale=scale)
                        pil_img = bitmap.to_pil()
                        bitmap.close()
                        page.close()
                        if pil_img.mode != "RGB":
                            converted = pil_img.convert("RGB")
                            pil_img.close()
                            pil_img = converted
                        images.append(pil_img)

                    doc.close()
                    doc = None

                fd, tmp_pdf_path = tempfile.mkstemp(prefix="compressed_", suffix=".pdf")
                os.close(fd)

                if images:
                    first_img = images[0]
                    rest_imgs = images[1:] if len(images) > 1 else []
                    first_img.save(
                        tmp_pdf_path,
                        format="PDF",
                        save_all=True,
                        append_images=rest_imgs,
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

                    saved_bytes = orig_size - new_size
                    saved_pct = round((saved_bytes / orig_size) * 100, 1)
                    log_event(
                        "pdf",
                        "INFO",
                        f"PDF optimize edildi: {os.path.basename(file_path)} ({orig_size // 1024} KB -> {new_size // 1024} KB, %{saved_pct} tasarruf)",
                    )
                    return {
                        "success": True,
                        "optimized": True,
                        "original_bytes": orig_size,
                        "compressed_bytes": new_size,
                        "saved_percent": saved_pct,
                        "saved_mb": round(saved_bytes / (1024 * 1024), 2),
                    }
                else:
                    if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                        os.remove(tmp_pdf_path)
                    return {
                        "success": True,
                        "optimized": False,
                        "message": "Belge zaten optimum boyutta, orijinal dosya korundu.",
                        "original_bytes": orig_size,
                        "compressed_bytes": orig_size,
                        "saved_percent": 0.0,
                    }
            except Exception as exc:
                log_event("pdf", "ERROR", f"PDF sıkıştırma hatası: {exc}")
                return {"success": False, "error": str(exc)}
            finally:
                for img in images:
                    try:
                        img.close()
                    except Exception as img_err:
                        log_event("pdf", "DEBUG", f"PIL image close warning: {img_err}")
                if doc is not None:
                    try:
                        doc.close()
                    except Exception as close_err:
                        log_event("pdf", "DEBUG", f"Pdf doc close warning: {close_err}")
                if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                    try:
                        os.remove(tmp_pdf_path)
                    except OSError as rm_err:
                        log_event("pdf", "DEBUG", f"Temp pdf cleanup warning: {rm_err}")

        return await asyncio.to_thread(_worker)


pdf_compressor = PDFCompressorService()
