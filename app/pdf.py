import io
import os
import threading

import pdf2image
import pdfplumber
import pytesseract
from PIL import Image

from app.config import configure_tesseract_from_config, load_config
from app.constants import DEFAULT_MAX_PAGES, THUMBNAILS_DIR
from app.logger import log_event

# Global thread-safety lock for pypdfium2 operations (PDFium C core is not thread-safe)
PDFIUM_LOCK = threading.Lock()


def extract_cover(file_path: str, file_hash: str) -> bool:
    """
    Extracts the first page of a PDF as a cover image.

    Args:
        file_path (str): Absolute path to the PDF file.
        file_hash (str): SHA256 hash of the file to use as filename.

    Returns:
        bool: True if successful or already exists, False otherwise.
    """
    thumbnails_dir = THUMBNAILS_DIR
    os.makedirs(thumbnails_dir, exist_ok=True)
    cover_path = os.path.join(thumbnails_dir, f"{file_hash}.jpg")

    if os.path.exists(cover_path):
        return True

    # Fast path: Try pypdfium2 first (ultra-fast C++ rendering, ~50ms, no Poppler binary required)
    try:
        import pypdfium2

        with PDFIUM_LOCK:
            doc = pypdfium2.PdfDocument(file_path)
            try:
                page = doc[0]
                bitmap = page.render(scale=2)
                try:
                    img = bitmap.to_pil()
                finally:
                    bitmap.close()
                    page.close()
                try:
                    if img.mode != "RGB":
                        converted = img.convert("RGB")
                        img.close()
                        img = converted
                    img.thumbnail((400, 560), Image.Resampling.LANCZOS)
                    img.save(cover_path, "JPEG", quality=88)
                    return True
                finally:
                    img.close()
            finally:
                doc.close()
    except Exception as fast_err:
        log_event(
            "pdf",
            "DEBUG",
            f"pypdfium2 cover extraction fallback to pdf2image: {fast_err}",
        )

    try:
        images = pdf2image.convert_from_path(file_path, first_page=1, last_page=1, dpi=200)

        if images:
            img = images[0]
            try:
                if img.mode != "RGB":
                    converted = img.convert("RGB")
                    img.close()
                    img = converted
                img.thumbnail((400, 560), Image.Resampling.LANCZOS)
                img.save(cover_path, "JPEG", quality=88)
                return True
            finally:
                for im in images:
                    try:
                        im.close()
                    except Exception as close_err:
                        log_event("pdf", "DEBUG", f"Cover image close note: {close_err}")
                try:
                    img.close()
                except Exception as close_err:
                    log_event("pdf", "DEBUG", f"Cover work image close note: {close_err}")
    except OSError as e:
        log_event(
            "pdf_processing",
            "ERROR",
            f"Poppler/OS hatası (kapak çıkartılırken, poppler kurulu olmayabilir veya erişim engellendi): {e}",
            file_hash=file_hash,
        )
    except Exception as e:
        log_event(
            "pdf_processing",
            "ERROR",
            f"Kapak çıkartılırken beklenmedik hata oluştu: {e}",
            file_hash=file_hash,
        )
    return False


def _extract_via_pypdfium2(file_path: str, max_p: int) -> str:
    """Fast extraction using pypdfium2 C++ rendering engine with smart page sampling."""
    try:
        import pypdfium2

        with PDFIUM_LOCK:
            doc = pypdfium2.PdfDocument(file_path)
            try:
                num_pages = len(doc)
                if max_p > 0 and num_pages > max_p:
                    front_count = max(1, min(num_pages, max_p - 2))
                    raw_indices = list(range(front_count))
                    if num_pages > 1:
                        raw_indices.append(num_pages - 2)
                    raw_indices.append(num_pages - 1)
                    indices = sorted(
                        dict.fromkeys(idx for idx in raw_indices if 0 <= idx < num_pages)
                    )
                else:
                    indices = list(range(num_pages if max_p <= 0 else min(num_pages, max_p)))

                extracted = []
                for i in indices:
                    page = doc[i]
                    tp = page.get_textpage()
                    try:
                        p_text = tp.get_text_range()
                    finally:
                        tp.close()
                        page.close()
                    if p_text and p_text.strip():
                        extracted.append(p_text)
                if extracted:
                    return "\n".join(extracted)
            finally:
                doc.close()
    except Exception as e:
        log_event("pdf", "DEBUG", f"pypdfium2 text extraction fallback: {e}")
    return ""


def get_pdf_page_count(file_path: str) -> int:
    """Return exact page count of a PDF file using pypdfium2 with pdfplumber fallback."""
    if not file_path or not os.path.exists(file_path):
        return 0
    try:
        import pypdfium2

        with PDFIUM_LOCK:
            doc = pypdfium2.PdfDocument(file_path)
            try:
                return int(len(doc))
            finally:
                doc.close()
    except Exception as fast_err:
        log_event("pdf", "DEBUG", f"pypdfium2 page count fallback: {fast_err}")
    try:
        with pdfplumber.open(file_path) as pdf:
            return int(len(pdf.pages))
    except Exception as fb_err:
        log_event("pdf", "DEBUG", f"pdfplumber page count fallback: {fb_err}")
        return 0


def _extract_via_ocr_stream(
    file_path: str, total_pages: int, max_p: int, configured_ocr: int
) -> str:
    """Stream OCR page-by-page to extract text from scanned documents while protecting RAM."""
    ocr_text_accum = []
    max_allowed_ocr = 30
    if max_p <= 0:
        limit_ocr = min(total_pages, max_allowed_ocr)
    else:
        limit_ocr = min(total_pages, configured_ocr if configured_ocr > 0 else max_allowed_ocr)

    log_event(
        "pdf_processing",
        "INFO",
        f"Sayfa akışlı OCR başlatılıyor, sayfa limiti: {limit_ocr}",
        path=file_path,
    )

    for page_idx in range(1, limit_ocr + 1):
        try:
            page_imgs = pdf2image.convert_from_path(
                file_path, first_page=page_idx, last_page=page_idx, dpi=150
            )
            if page_imgs:
                ocr_text = pytesseract.image_to_string(
                    page_imgs[0], lang="tur+eng", config="--psm 1"
                )
                if ocr_text and ocr_text.strip():
                    ocr_text_accum.append(ocr_text)
                del page_imgs
        except Exception as p_err:
            log_event(
                "pdf_processing",
                "WARNING",
                f"Sayfa {page_idx} OCR hatası: {p_err}",
                path=file_path,
            )
            continue

    return "\n".join(ocr_text_accum)


def _run_ocr_fallback(file_path: str, total_pages: int, max_p: int, config: dict) -> str:
    """Run Tesseract OCR stream fallback if OCR is installed."""
    configured_ocr = int(config.get("ocr_pages", 20) or 20)
    try:
        pytesseract.get_tesseract_version()
        return _extract_via_ocr_stream(file_path, total_pages, max_p, configured_ocr)
    except pytesseract.TesseractNotFoundError:
        log_event(
            "pdf_processing",
            "WARNING",
            f"Tesseract OCR sistemde bulunamadı: {file_path}",
        )
    except OSError as e:
        log_event(
            "pdf_processing",
            "WARNING",
            f"OCR poppler/dönüştürme hatası: {e}",
            path=file_path,
        )
    except Exception as e:
        log_event(
            "pdf_processing",
            "WARNING",
            f"OCR işlemleri sırasında hata: {e}",
            path=file_path,
        )
    return ""


def _extract_via_pdfplumber(file_path: str, max_p: int, config: dict) -> str:
    """Extract text using pdfplumber with OCR fallback when text is sparse."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            pages_to_extract = pdf.pages if max_p <= 0 else pdf.pages[:max_p]
            for page in pages_to_extract:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            if len(text.strip()) < 200:
                ocr_res = _run_ocr_fallback(file_path, len(pdf.pages), max_p, config)
                if ocr_res:
                    text += ocr_res + "\n"
    except FileNotFoundError:
        log_event("pdf_processing", "ERROR", f"PDF dosyası bulunamadı: {file_path}")
    except OSError as e:
        log_event(
            "pdf_processing",
            "ERROR",
            f"PDF okunurken OS/Dosya sistemi hatası: {e}",
            path=file_path,
        )
    except Exception as e:
        log_event(
            "pdf_processing",
            "ERROR",
            f"PDF metin çıkarımı sırasında genel hata: {e}",
            path=file_path,
        )
    return text


def extract_text_from_pdf(file_path: str, max_pages: int | None = None) -> str:
    """
    Extracts text from a PDF file. If the extracted text is too short,
    falls back to Tesseract OCR.

    Args:
        file_path (str): Path to the PDF file.
        max_pages (int, optional): Maximum pages to extract. If 0 or None, extracts all pages.

    Returns:
        str: Extracted text content.
    """
    config = load_config()
    configure_tesseract_from_config(config)

    max_p = config.get("max_pages", DEFAULT_MAX_PAGES) if max_pages is None else max_pages

    # 1. Fast path: pypdfium2
    text = _extract_via_pypdfium2(file_path, max_p)
    if len(text.strip()) >= 200:
        return text

    # 2. Secondary path: pdfplumber with OCR fallback for scanned PDFs
    return _extract_via_pdfplumber(file_path, max_p, config)


def prepare_cover_image(content: bytes, max_image_pixels: int = 178956970, **kwargs) -> Image.Image:
    """
    Validates and prepares an uploaded image for use as a cover.

    Args:
        content (bytes): Raw image bytes.
        max_image_pixels (int): Maximum allowed resolution.

    Returns:
        Image.Image: PIL Image object.

    Raises:
        ValueError: If image is invalid or too large.
    """
    limit = kwargs.get("MAX_IMAGE_PIXELS", max_image_pixels)
    try:
        with Image.open(io.BytesIO(content)) as probe:
            if probe.width * probe.height > limit:
                raise ValueError("Image resolution too large")
            probe.verify()
        img = Image.open(io.BytesIO(content))
        if img.width * img.height > limit:
            img.close()
            raise ValueError("Image resolution too large")
        img.load()
    except Image.DecompressionBombError:
        log_event(
            "pdf_processing",
            "WARNING",
            "Görsel boyutu aşırı büyük (DecompressionBombError)",
        )
        raise ValueError("Image too large") from None
    except ValueError:
        raise
    except (OSError, SyntaxError) as e:
        log_event("pdf_processing", "WARNING", f"Geçersiz veya bozuk görsel dosyası: {e}")
        raise ValueError("Invalid image file") from None

    if img.mode != "RGB":
        converted = img.convert("RGB")
        img.close()
        img = converted
    return img


def _calculate_vision_page_indices(
    total: int, max_pages: int, one_based: bool = False
) -> list[int]:
    """Calculate front and tail page indices for vision analysis."""
    offset = 1 if one_based else 0
    if max_pages <= 0 or total <= max_pages:
        return list(range(offset, total + offset))

    front = max(1, max_pages - 2)
    front_indices = list(range(offset, front + offset))
    tail_indices = [total - 2 + offset, total - 1 + offset]
    return front_indices + tail_indices


def _render_pages_pdfium(file_path: str, max_pages: int, max_dim: int) -> list[Image.Image]:
    """Render PDF pages using high-speed pypdfium2 C++ engine under global PDFIUM_LOCK."""
    import pypdfium2

    images: list[Image.Image] = []
    with PDFIUM_LOCK:
        doc = pypdfium2.PdfDocument(file_path)
        try:
            total = len(doc)
            page_indices = _calculate_vision_page_indices(total, max_pages, one_based=False)

            for idx in page_indices:
                if 0 <= idx < total:
                    page = doc[idx]
                    bitmap = page.render(scale=1.5)
                    try:
                        pil_img = bitmap.to_pil()
                    finally:
                        bitmap.close()
                        page.close()
                    pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                    if pil_img.mode != "RGB":
                        converted = pil_img.convert("RGB")
                        pil_img.close()
                        pil_img = converted
                    images.append(pil_img)
        except Exception:
            for im in images:
                try:
                    im.close()
                except Exception as close_err:
                    log_event("pdf", "DEBUG", f"Vision image cleanup note: {close_err}")
            raise
        finally:
            doc.close()

    return images


def _render_pages_pdf2image(file_path: str, max_pages: int, max_dim: int) -> list[Image.Image]:
    """Fallback rendering PDF pages using pdfplumber and pdf2image."""
    import pdfplumber

    images: list[Image.Image] = []
    with pdfplumber.open(file_path) as pdf:
        total = len(pdf.pages)

    indices = _calculate_vision_page_indices(total, max_pages, one_based=True)
    for p_no in indices:
        if 1 <= p_no <= total:
            imgs = pdf2image.convert_from_path(file_path, first_page=p_no, last_page=p_no, dpi=130)
            if imgs:
                img = imgs[0]
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                if img.mode != "RGB":
                    converted = img.convert("RGB")
                    img.close()
                    img = converted
                images.append(img)
    return images


def render_pdf_vision_pages(
    file_path: str,
    max_pages: int = 20,
    max_dim: int = 1200,
    **kwargs,
) -> list[Image.Image]:
    """
    Renders selected PDF pages as optimized PIL Images for vision/multimodal models.
    Supports pypdfium2 (ultra-fast C++) with pdf2image as fallback.
    """
    if not os.path.exists(file_path):
        return []

    try:
        images = _render_pages_pdfium(file_path, max_pages, max_dim)
        if images:
            return images
    except Exception as fast_err:
        log_event(
            "pdf",
            "DEBUG",
            f"pypdfium2 vision rendering fallback to pdf2image: {fast_err}",
        )

    try:
        return _render_pages_pdf2image(file_path, max_pages, max_dim)
    except Exception as e:
        log_event(
            "pdf_processing",
            "WARNING",
            f"Vision sayfaları dönüştürülürken hata: {e}",
            path=file_path,
        )

    return []


def create_vision_pdf(
    file_path: str,
    output_path: str | None = None,
    max_pages: int = 20,
    max_dim: int = 1200,
    quality: int = 82,
) -> str | None:
    """
    Creates an optimized, lightweight multi-page PDF from rendered vision pages.
    Ideal for uploading to Gemini / Vision API when text extraction and OCR fail.
    """
    import tempfile

    images = render_pdf_vision_pages(
        file_path, max_pages=max_pages, max_dim=max_dim, quality=quality
    )
    if not images:
        return None

    if not output_path:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vision.pdf")
        output_path = tmp.name
        tmp.close()

    try:
        first = images[0]
        rest = images[1:] if len(images) > 1 else []
        first.save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=rest,
            quality=quality,
        )
        return output_path
    except Exception as e:
        log_event("pdf_processing", "ERROR", f"Vision PDF kaydedilemedi: {e}", path=file_path)
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError as rm_err:
                log_event(
                    "pdf",
                    "DEBUG",
                    f"Could not remove temp vision pdf {output_path}: {rm_err}",
                )
        return None
    finally:
        for img in images:
            try:
                img.close()
            except Exception as close_err:
                log_event("pdf", "DEBUG", f"Image close warning: {close_err}")
