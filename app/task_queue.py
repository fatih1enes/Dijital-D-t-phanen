"""Internal task queue with ThreadPoolExecutor for CPU-bound PDF processing.

Architecture
~~~~~~~~~~~~
GIL Bypass & Threading:
    ``ThreadPoolExecutor`` runs background task processing on separate OS threads.
    Heavy CPU/IO tasks (like PDF extraction, image resizing, pytesseract OCR execution,
    and HTTP client requests) release the GIL, ensuring the main process's ``asyncio``
    event loop remains perfectly free and responsive.

Environment Stability:
    Threads run in the same memory space as the main process. This completely avoids
    Windows multiprocessing 'spawn' bugs, pickling errors, and virtual environment (venv)
    context loss, ensuring a rock-solid background pipeline.

Queue-Based Ordering:
    ``asyncio.Queue`` ensures uploads are processed sequentially (one at a time).
    For a local, single-user app this conserves resources and prevents race
    conditions on the filesystem or external API rate limits.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.constants import DEFAULT_GEMINI_MODEL, LIBRARY_ROOT, MAX_CONCURRENT_TASKS
from app.prompts import build_pdf_analysis_prompt
from app.tasks import GeminiRateLimiter
from app.utils import (
    get_file_hash_from_path,
    mask_sensitive_data,
    sanitize_dirname,
    sanitize_filename,
)

logger = logging.getLogger(__name__)

# Shared rate limiter across task queue jobs to respect Gemini RPM and TPM quotas
_queue_rate_limiter = GeminiRateLimiter(rpm=13, tpm=210000)

FIELD_KITAP_ADI = "kitap_adi"
FIELD_YAZAR = "yazar"
FIELD_KATEGORI = "kategori"
FIELD_ALT_KATEGORI = "alt_kategori"
FIELD_OZET = "ozet"
FIELD_ANAHTAR_KELIMELER = "anahtar_kelimeler"
VAL_UNKNOWN = "Bilinmeyen"
VAL_UNKNOWN_AUTHOR = "Bilinmeyen Yazar"
VAL_NOT_KNOWN = "Bilinmiyor"
STATUS_PROCESSING = "processing"
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
LOG_CATEGORY_AI_ANALYZE = "ai_analyze"
LOG_CATEGORY_PDF = "pdf"
LOG_CATEGORY_DOCUMENT = "document"
LOG_CATEGORY_FILESYSTEM = "filesystem"
LOG_CATEGORY_UPLOAD = "upload"
LOG_CATEGORY_DATABASE = "database"
LVL_INFO = "INFO"
LVL_WARNING = "WARNING"
LVL_ERROR = "ERROR"
LVL_DEBUG = "DEBUG"
KEY_FILENAME = "filename"
KEY_FILE_HASH = "file_hash"


def _make_fallback_metadata(filename: str, ozet: str) -> dict:
    """Construct default metadata dict when AI extraction fails."""
    clean_stem = re.sub(r"\.(pdf|epub|txt)$", "", filename, flags=re.I)
    return {
        FIELD_KITAP_ADI: clean_stem,
        FIELD_YAZAR: VAL_UNKNOWN_AUTHOR,
        FIELD_KATEGORI: VAL_UNKNOWN,
        FIELD_ALT_KATEGORI: VAL_UNKNOWN,
        FIELD_OZET: ozet,
        FIELD_ANAHTAR_KELIMELER: "",
    }


# ---------------------------------------------------------------------------
# Background Worker Functions (ThreadPoolExecutor)
# ---------------------------------------------------------------------------
# These worker functions execute on background worker threads managed by
# ThreadPoolExecutor. Heavy CPU and I/O tasks (PDF parsing via pdfplumber,
# PIL image conversion, and AI API requests) release Python's GIL so that
# the main asyncio event loop remains fully responsive.
# ---------------------------------------------------------------------------
FULL_TEXT_EXT = ".full.txt"


def _extract_full_text_in_background(
    pdf_path: str, final_path: str, filename: str, task_id: str | None = None
) -> None:
    """Background daemon worker to index full book text without blocking UI / ingestion."""
    lower_final = final_path.lower()
    if lower_final.endswith((".txt", FULL_TEXT_EXT)):
        return
    try:
        from app.logger import log_event

        log_event(
            "pdf",
            "INFO",
            f"Tam metin arşivi arka planda indeksleniyor: {filename}",
            task_id=task_id,
        )
        if lower_final.endswith(".epub"):
            from app.epub import extract_text_from_epub

            full_text = extract_text_from_epub(pdf_path, max_chars=0)
        else:
            from app.pdf import extract_text_from_pdf

            full_text = extract_text_from_pdf(pdf_path, max_pages=0)
        if full_text and full_text.strip():
            text_path = final_path + FULL_TEXT_EXT
            try:
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
            except Exception as write_err:
                log_event("pdf", "DEBUG", f"Full-text cache file write warning: {write_err}")
            log_event(
                "pdf",
                "INFO",
                f"Tam metin arşivi başarıyla tamamlandı ({len(full_text)} karakter): {filename}",
                task_id=task_id,
                char_count=len(full_text),
            )
    except Exception as e:
        try:
            from app.logger import log_event

            log_event(
                "pdf",
                "WARNING",
                f"Tam metin arşivi oluşturulurken hata ({filename}): {e}",
                task_id=task_id,
                error=str(e),
            )
        except Exception as log_err:
            import logging

            logging.debug("Could not log background indexing error: %s", log_err)


def _extract_document_text(
    tmp_path: str, is_epub: bool, is_txt: bool, max_pages: int
) -> tuple[str, str]:
    """Extract document text based on format (EPUB, TXT, or PDF)."""
    from app.epub import extract_text_from_epub, extract_text_from_txt
    from app.pdf import extract_text_from_pdf

    if is_epub:
        return extract_text_from_epub(tmp_path, max_chars=25000), "EPUB"
    if is_txt:
        return extract_text_from_txt(tmp_path, max_chars=25000), "TXT"
    return extract_text_from_pdf(tmp_path, max_pages=max_pages), "PDF"


def _extract_and_save_cover(tmp_path: str, file_hash: str, is_epub: bool, is_txt: bool) -> bool:
    """Extract and save book cover thumbnail."""
    if is_epub:
        from app.epub import extract_cover_from_epub

        return extract_cover_from_epub(tmp_path, file_hash)
    if is_txt:
        return False
    from app.pdf import extract_cover

    return extract_cover(tmp_path, file_hash)


def _finalize_library_placement(tmp_path: str, filename: str, kategori: str, file_hash: str) -> str:
    """Archive processed file to category directory in library, resolving name collisions."""
    safe_kategori = sanitize_dirname(kategori or "Bilinmeyen")
    dest_dir = os.path.join(LIBRARY_ROOT, safe_kategori)
    os.makedirs(dest_dir, exist_ok=True)

    base_safe_name = sanitize_filename(filename)
    final_path = os.path.join(dest_dir, base_safe_name)

    if os.path.exists(final_path):
        existing_hash = get_file_hash_from_path(final_path)
        if existing_hash != file_hash:
            name_stem, ext = os.path.splitext(base_safe_name)
            counter = 1
            while os.path.exists(final_path):
                new_name = f"{name_stem}_{counter}{ext}"
                final_path = os.path.join(dest_dir, new_name)
                counter += 1

    shutil.copy2(tmp_path, final_path)
    return final_path


def _prepare_vision_pdf(
    tmp_path: str,
    filename: str,
    task_id: str,
    char_len: int,
    is_epub: bool,
    is_txt: bool,
    config: dict,
) -> str | None:
    """Attempt to generate vision PDF pages for scanned documents with insufficient text."""
    if is_epub or is_txt or char_len >= 200:
        return None
    try:
        from app.logger import log_event
        from app.pdf import create_vision_pdf
        from app.tasks import update_task_status

        v_pages = int((config or {}).get("vision_pages", 20) or 20)
        v_dim = int((config or {}).get("vision_max_image_dim", 1200) or 1200)
        v_qual = int((config or {}).get("vision_jpeg_quality", 82) or 82)
        log_event(
            LOG_CATEGORY_AI_ANALYZE,
            LVL_INFO,
            f"Vision analizi devreye alınıyor: {filename}",
            task_id=task_id,
        )
        update_task_status(task_id, STATUS_PROCESSING, 40, "Görsel analiz (Vision) hazırlanıyor...")
        return create_vision_pdf(tmp_path, max_pages=v_pages, max_dim=v_dim, quality=v_qual)
    except Exception as v_err:
        from app.logger import log_event

        log_event(
            LOG_CATEGORY_AI_ANALYZE,
            LVL_WARNING,
            f"Vision PDF oluşturulamadı ({v_err}), metinle devam ediliyor",
            task_id=task_id,
        )
        return None


def _analyze_with_ai_safely(
    task_id: str,
    filename: str,
    text_for_ai: str,
    provider: str,
    api_key: str,
    config: dict,
    model_name: str | None,
    base_url: str | None,
    vision_pdf_path: str | None,
) -> dict:
    """Invoke standalone AI model analysis with automatic vision PDF cleanup."""
    from app.tasks import update_task_status

    active_model = model_name or (DEFAULT_GEMINI_MODEL if provider == "gemini" else provider)
    update_task_status(
        task_id,
        STATUS_PROCESSING,
        50,
        f"Yapay zeka analizi yapılıyor ({provider.upper()} - {active_model})...",
    )
    try:
        return _analyze_pdf_standalone(
            filename,
            text_for_ai,
            provider,
            api_key,
            config,
            model_name,
            base_url,
            task_id=task_id,
            pdf_path=vision_pdf_path,
        )
    finally:
        if vision_pdf_path and os.path.exists(vision_pdf_path):
            try:
                os.unlink(vision_pdf_path)
            except Exception as unlink_err:
                from app.logger import log_event

                log_event(
                    LOG_CATEGORY_PDF,
                    LVL_DEBUG,
                    f"Vision PDF unlink warning: {unlink_err}",
                )


def _handle_full_text_and_indexing(
    final_path: str,
    filename: str,
    task_id: str,
    file_hash: str,
    text_for_ai: str,
) -> list:
    """Save full-text cache, start background full-book extraction, and return chunks."""
    from app.logger import log_event

    if not final_path.lower().endswith((".txt", FULL_TEXT_EXT)):
        text_path = final_path + FULL_TEXT_EXT
        try:
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text_for_ai)
        except Exception as write_err:
            log_event(
                LOG_CATEGORY_PDF,
                LVL_DEBUG,
                f"Initial full-text write warning: {write_err}",
            )

        threading.Thread(
            target=_extract_full_text_in_background,
            args=(final_path, final_path, filename, task_id),
            daemon=True,
        ).start()

    try:
        from app.services.chunking_service import DocumentChunker

        return DocumentChunker.chunk_document(final_path, file_hash)
    except Exception as chunk_err:
        log_event(
            LOG_CATEGORY_PDF,
            LVL_WARNING,
            f"Metin parçalama hatası: {chunk_err}",
            task_id=task_id,
        )
        return []


def _process_pdf_in_worker(
    task_id: str,
    tmp_path: str,
    filename: str,
    file_hash: str,
    provider: str,
    api_key: str,
    config: dict,
    model_name: str | None,
    base_url: str | None,
) -> dict:
    """Run CPU and I/O-bound document processing in a background worker thread."""
    from app.logger import log_event
    from app.tasks import update_task_status

    lower_fn = filename.lower()
    if (
        lower_fn.endswith((FULL_TEXT_EXT, ".pdf.txt", ".epub.txt", ".txt.txt", ".cache.txt"))
        or ".pdf." in lower_fn
        or ".epub." in lower_fn
        or ".txt." in lower_fn
    ):
        raise ValueError(
            f"Önbellek veya türetilmiş metin dosyaları kitap olarak işlenemez: {filename}"
        )

    is_epub = lower_fn.endswith(".epub")
    is_txt = lower_fn.endswith(".txt")

    # Step 1: Extract preview text
    max_pages = config.get("max_pages", 20)
    update_task_status(task_id, STATUS_PROCESSING, 25, "Belge okunuyor...")
    text_for_ai, doc_type = _extract_document_text(tmp_path, is_epub, is_txt, max_pages)
    char_len = len(text_for_ai.strip())
    log_event(
        LOG_CATEGORY_DOCUMENT,
        LVL_INFO,
        f"{doc_type} metni okundu ({char_len} karakter): {filename}",
        task_id=task_id,
        char_count=char_len,
    )

    # Step 2: Multimodal vision fallback for scanned documents
    vision_pdf_path = _prepare_vision_pdf(
        tmp_path, filename, task_id, char_len, is_epub, is_txt, config
    )

    # Step 3: Standalone AI analysis
    data = _analyze_with_ai_safely(
        task_id,
        filename,
        text_for_ai,
        provider,
        api_key,
        config,
        model_name,
        base_url,
        vision_pdf_path,
    )

    # Step 4: Extract cover
    update_task_status(task_id, STATUS_PROCESSING, 70, "Kapak görseli hazırlanıyor...")
    has_cover = _extract_and_save_cover(tmp_path, file_hash, is_epub, is_txt)
    data["has_cover"] = 1 if has_cover else 0
    if has_cover:
        log_event(
            LOG_CATEGORY_DOCUMENT,
            LVL_INFO,
            f"Kapak görseli hazırlandı: {filename}",
            task_id=task_id,
        )

    # Step 5: Archive file into library
    update_task_status(task_id, STATUS_PROCESSING, 80, "Dosya kütüphaneye arşivleniyor...")
    final_path = _finalize_library_placement(
        tmp_path, filename, data.get(FIELD_KATEGORI, VAL_UNKNOWN), file_hash
    )
    log_event(
        LOG_CATEGORY_FILESYSTEM,
        LVL_INFO,
        f"Dosya kütüphaneye yerleştirildi: {final_path}",
        task_id=task_id,
        path=final_path,
    )

    # Step 6 & 7: Full text caching and chunking
    chunks = _handle_full_text_and_indexing(final_path, filename, task_id, file_hash, text_for_ai)

    return {
        "data": data,
        "text_for_ai": text_for_ai,
        "final_path": final_path,
        "chunks": chunks,
    }


def extract_and_parse_json(text: str) -> dict:
    """Extract and parse JSON object from AI model response safely.

    Preserves internal newlines in strings, handles markdown code fences,
    and strips trailing commas without mangling valid JSON.
    """
    if not text or not text.strip():
        raise ValueError("Empty response from AI provider")

    clean_text = text.strip()

    # Match markdown code block if present
    json_match = re.search(r"```(?:json)?\s*(\{[^`]*\})\s*```", clean_text, re.DOTALL)
    if json_match:
        candidate = json_match.group(1).strip()
    else:
        first_brace = clean_text.find("{")
        last_brace = clean_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            candidate = clean_text[first_brace : last_brace + 1].strip()
        else:
            candidate = clean_text

    # 1. Direct parse attempt (safest, retains internal newlines in strings)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as jde:
        logger.debug("Candidate direct parse failed: %s, attempting sanitization", jde)

    # 2. Strip trailing commas before closing braces/brackets
    sanitized = re.sub(r",\s*([\}\]])", r"\1", candidate)
    try:
        return json.loads(sanitized)
    except json.JSONDecodeError as jde:
        logger.debug("Sanitized json parse failed: %s, attempting normalization", jde)

    # 3. Fallback: normalize raw unescaped control chars if model emitted bad newlines
    normalized = re.sub(r"[\r\n\t]+", " ", sanitized)
    return json.loads(normalized)


def _is_permanent_ai_error(err_str: str) -> bool:
    """Check if the error message represents a permanent non-retryable failure."""
    lower = err_str.lower()
    permanent_keywords = [
        "401",
        "403",
        "api_key_invalid",
        "api key not valid",
        "blocked response",
        "safety rating",
    ]
    return any(k in lower for k in permanent_keywords)


def _is_retryable_quota_error(text: str) -> bool:
    """Check if the error is a transient rate-limit / quota exhaustion error."""
    return any(k in text for k in ("Resource Exhausted", "429", "Quota exceeded"))


def _execute_ai_attempt(
    ai_service: Any,
    prompt: str,
    provider: str,
    api_key: str,
    model_name: str | None,
    base_url: str | None,
    google_search: bool,
    pdf_path: str | None,
    cascade_active: bool,
    rate_limiter: Any,
) -> str:
    """Execute a single attempt to generate text from the AI provider."""
    if provider == "gemini" and not cascade_active:
        est_tokens = max(1, int(len(prompt) / 2.0))
        rate_limiter.wait_if_needed(estimated_tokens=est_tokens)

    return ai_service.generate_text(
        prompt,
        provider,
        api_key,
        model=model_name,
        base_url=base_url,
        google_search_grounding=google_search,
        pdf_path=pdf_path,
    )


def _process_ai_result_or_raise(
    result_text: str, attempt: int, max_retries: int, delay: float
) -> float:
    """Handle error response from AI provider, back off if retryable, or raise."""
    if _is_permanent_ai_error(result_text):
        raise ValueError(result_text)
    if _is_retryable_quota_error(result_text) and attempt < max_retries - 1:
        time.sleep(delay)
        return delay * 2.0
    raise ValueError(result_text)


def _handle_attempt_exception(
    exc: Exception, attempt: int, max_retries: int, delay: float
) -> float:
    """Handle exception during AI call, back off if retryable, or re-raise."""
    err_msg = str(exc)
    if _is_permanent_ai_error(err_msg):
        raise exc
    if attempt < max_retries - 1:
        time.sleep(delay)
        return delay * 2.0
    raise exc


def _call_ai_with_retry(
    ai_service: Any,
    prompt: str,
    provider: str,
    api_key: str,
    model_name: str | None,
    base_url: str | None,
    google_search: bool,
    pdf_path: str | None,
    cascade_active: bool,
    rate_limiter: Any,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> str:
    """Execute AI text generation with exponential backoff on 429 quota exhaustion."""
    effective_max_retries = 1 if (cascade_active and provider == "gemini") else max_retries
    result_text = ""
    current_delay = float(retry_delay)

    for attempt in range(effective_max_retries):
        try:
            result_text = _execute_ai_attempt(
                ai_service,
                prompt,
                provider,
                api_key,
                model_name,
                base_url,
                google_search,
                pdf_path,
                cascade_active,
                rate_limiter,
            )

            if result_text.startswith("Error"):
                current_delay = _process_ai_result_or_raise(
                    result_text, attempt, effective_max_retries, current_delay
                )
                continue

            return result_text

        except Exception as exc:
            if isinstance(exc, ValueError) and str(exc) == result_text:
                raise
            current_delay = _handle_attempt_exception(
                exc, attempt, effective_max_retries, current_delay
            )

    if not result_text or not result_text.strip():
        raise ValueError("Empty response from AI provider")
    return result_text


def _analyze_pdf_standalone(
    filename: str,
    text: str,
    provider: str,
    api_key: str,
    config: dict | None,
    model_name: str | None,
    base_url: str | None,
    task_id: str | None = None,
    pdf_path: str | None = None,
) -> dict:
    """Standalone AI document analysis using prompts module and retry helper."""
    from app.config import is_real_api_key, load_config, resolve_ai_credentials
    from app.logger import log_event
    from app.services.ai_service import AIService

    cfg = config or load_config()
    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=provider,
        api_key=api_key,
        model=model_name,
        base_url=base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    if not api_key and provider not in ["ollama", "lmstudio"]:
        return _make_fallback_metadata(filename, "Analiz başarısız (API anahtarı yok).")

    ai_service = AIService()
    max_chars = cfg.get("ai_max_chars", 50000)
    is_scanned = bool(pdf_path and len(text.strip()) < 200)
    prompt = build_pdf_analysis_prompt(
        filename, text, is_scanned_pdf=is_scanned, max_chars=max_chars
    )

    try:
        result_text = _call_ai_with_retry(
            ai_service=ai_service,
            prompt=prompt,
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            google_search=bool(cfg.get("google_search_grounding", False)),
            pdf_path=pdf_path,
            cascade_active=bool(cfg.get("gemini_cascade_mode", True)),
            rate_limiter=_queue_rate_limiter,
        )

        safe_preview = mask_sensitive_data(result_text[:2000])
        log_event(
            "ai_raw",
            "INFO",
            f"Yapay zeka ham yanıtı alındı ({len(result_text)} karakter)",
            task_id=task_id,
            raw_response=safe_preview,
        )

        result = extract_and_parse_json(result_text)
        for key in [
            FIELD_KITAP_ADI,
            FIELD_YAZAR,
            FIELD_KATEGORI,
            FIELD_ALT_KATEGORI,
            FIELD_OZET,
            FIELD_ANAHTAR_KELIMELER,
        ]:
            if key not in result:
                result[key] = VAL_NOT_KNOWN

        log_event(
            LOG_CATEGORY_AI_ANALYZE,
            "INFO",
            f"Kitap analizi başarıyla tamamlandı: '{result.get(FIELD_KITAP_ADI)}' | Yazar: {result.get(FIELD_YAZAR)} [{result.get(FIELD_KATEGORI)}]",
            task_id=task_id,
            metadata=result,
        )
        return result

    except json.JSONDecodeError as jde:
        log_event(
            LOG_CATEGORY_AI_ANALYZE,
            "WARNING",
            f"AI yanıtı JSON formatında ayrıştırılamadı ({jde}). Dosya adı kullanılıyor.",
            task_id=task_id,
        )
        return _make_fallback_metadata(
            filename, "Analiz çıktısı ayrıştırılamadı (Geçersiz JSON formatı)."
        )
    except ValueError as ve:
        safe_err = mask_sensitive_data(str(ve))
        log_event(
            LOG_CATEGORY_AI_ANALYZE,
            "ERROR",
            f"Yapay zeka analiz hatası: {safe_err}",
            task_id=task_id,
            error=safe_err,
        )
        return _make_fallback_metadata(
            filename, f"Analiz başarısız ({provider.capitalize()} hatası)."
        )
    except Exception as e:
        safe_err = mask_sensitive_data(str(e))
        log_event(
            LOG_CATEGORY_AI_ANALYZE,
            "ERROR",
            f"Yapay zeka analizi sırasında beklenmedik hata: {safe_err}",
            task_id=task_id,
            error=safe_err,
        )
        return _make_fallback_metadata(
            filename, "Analiz sırasında beklenmedik bir sistem hatası oluştu."
        )


# ---------------------------------------------------------------------------
# Task Queue (runs in the main process)
# ---------------------------------------------------------------------------


async def _save_book_and_index_chunks(
    bg_db: Any,
    task_id: str,
    task_data: dict,
    final_path: str,
    data: dict,
    result: dict,
) -> dict:
    """Persist book entry to SQLite and generate FTS5 search index chunks."""
    from app.logger import log_event
    from app.tasks import update_task_status

    update_task_status(
        task_id,
        STATUS_PROCESSING,
        92,
        "Veritabanı kaydı oluşturuluyor...",
        log_state="INFO",
        task_data=data,
    )

    chunks = result.get("chunks")
    if chunks is None:
        try:
            from app.services.chunking_service import DocumentChunker

            chunks = await asyncio.to_thread(
                DocumentChunker.chunk_document, final_path, task_data["file_hash"]
            )
        except Exception as chunk_gen_err:
            log_event(
                LOG_CATEGORY_DATABASE,
                "DEBUG",
                f"Chunk üretimi atlandı ({task_data['filename']}): {chunk_gen_err}",
            )
            chunks = []

    file_size = 0
    if final_path and os.path.exists(final_path):
        try:
            file_size = os.path.getsize(final_path)
        except OSError as sz_err:
            log_event(LOG_CATEGORY_DATABASE, "DEBUG", f"Dosya boyutu okunamadı: {sz_err}")

    page_count = int(data.get("sayfa_sayisi") or 0)
    if page_count <= 0 and final_path:
        if final_path.lower().endswith(".pdf"):
            from app.pdf import get_pdf_page_count

            page_count = await asyncio.to_thread(get_pdf_page_count, final_path)
        elif chunks and isinstance(chunks, list):
            page_count = max((int(c.get("sayfa_no") or 0) for c in chunks), default=0)

    book_entry = {
        **data,
        "dosya_adi": task_data["filename"],
        "dosya_hash": task_data["file_hash"],
        "dosya_yolu": final_path,
        "sayfa_sayisi": page_count,
        "dosya_boyutu": file_size,
    }
    await bg_db.add_book(book_entry)

    if chunks and isinstance(chunks, list):
        try:
            update_task_status(
                task_id,
                STATUS_PROCESSING,
                95,
                "Kitap pasajları, vektör gömmeleri ve FTS5 arama dizini oluşturuluyor...",
                log_state="INFO",
            )
            from app.services.chunking_service import index_document_chunks
            from app.services.embedding_service import embedding_service

            chunk_texts = [str(c.get("metin", "")) for c in chunks]
            embeddings, emb_model = await asyncio.to_thread(
                embedding_service.generate_semantic_embeddings_batch,
                chunk_texts,
                task_data.get("provider"),
                task_data.get("api_key"),
                task_data.get("base_url"),
            )
            indexed_count = await index_document_chunks(
                bg_db, chunks, embeddings=embeddings, embedding_model=emb_model
            )
            log_event(
                LOG_CATEGORY_DATABASE,
                "INFO",
                f"FTS5 + Vektör pasaj indeksi tamamlandı ({indexed_count} pasaj): {task_data['filename']}",
                task_id=task_id,
                chunk_count=indexed_count,
            )
        except Exception as chunk_err:
            log_event(
                LOG_CATEGORY_DATABASE,
                "WARNING",
                f"Metin pasajları indekslenirken hata oluştu ({task_data['filename']}): {chunk_err}",
                task_id=task_id,
            )

    return book_entry


async def _notify_task_completion(
    task_id: str,
    task_data: dict,
    final_path: str,
    data: dict,
    book_entry: dict,
) -> None:
    """Clear caches, publish BookUploadedEvent, and mark background task as success."""
    from fastapi_cache import FastAPICache

    from app.event_bus import BookUploadedEvent, event_bus
    from app.logger import log_event
    from app.tasks import update_task_status

    provider = task_data.get("provider")
    log_event(
        LOG_CATEGORY_UPLOAD,
        "INFO",
        f"Kitap kütüphaneye başarıyla kaydedildi: '{data.get(FIELD_KITAP_ADI)}' ({data.get(FIELD_KATEGORI)})",
        task_id=task_id,
        filename=task_data["filename"],
        file_hash=task_data["file_hash"],
        kitap_adi=data.get(FIELD_KITAP_ADI),
        yazar=data.get(FIELD_YAZAR),
        kategori=data.get(FIELD_KATEGORI),
        provider=provider,
    )

    await FastAPICache.clear(namespace="books")
    await FastAPICache.clear(namespace="stats")

    update_task_status(
        task_id,
        STATUS_SUCCESS,
        100,
        f"Kitap başarıyla eklendi: {data.get(FIELD_KITAP_ADI, VAL_NOT_KNOWN)}",
        log_state="INFO",
        task_data=book_entry,
    )

    await event_bus.publish(
        BookUploadedEvent(
            file_hash=task_data["file_hash"],
            kitap_adi=data.get(FIELD_KITAP_ADI, ""),
            yazar=data.get(FIELD_YAZAR, ""),
            kategori=data.get(FIELD_KATEGORI, ""),
            dosya_yolu=final_path,
            dosya_adi=task_data["filename"],
        )
    )


async def _cleanup_temp_file_safely(tmp_path: str | None) -> None:
    """Safely remove a temporary file with retry logic for Windows file locking."""
    if not tmp_path or not os.path.exists(tmp_path):
        return
    deleted = False
    for _ in range(4):
        try:
            os.remove(tmp_path)
            deleted = True
            break
        except OSError:
            await asyncio.sleep(0.15)
    if not deleted:
        try:
            os.remove(tmp_path)
        except OSError as _rm_err:
            from app.logger import log_event as _log

            _log(
                LOG_CATEGORY_FILESYSTEM,
                "WARNING",
                f"Geçici PDF dosyası silinemedi ({tmp_path}): {_rm_err}",
            )


class TaskQueue:
    """Lightweight internal task manager using ``asyncio.Queue`` + ``ThreadPoolExecutor``.

    - ``enqueue()`` pushes jobs onto the queue (called from upload endpoint).
    - ``worker_loop()`` runs forever as a ``lifespan`` background task,
      pulling jobs one-by-one and dispatching the CPU-heavy part to a
      separate thread via ``loop.run_in_executor()``.
    """

    def __init__(self, max_workers: int | None = None):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        # Configurable concurrency via MAX_CONCURRENT_TASKS (default 1 to conserve resources)
        workers = max_workers if max_workers is not None else MAX_CONCURRENT_TASKS
        self._max_workers: int = max(1, workers)
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

    def ensure_active_loop(self) -> None:
        """Rebind internal asyncio.Queue and ThreadPoolExecutor if event loop changed or restarted."""
        running_loop = asyncio.get_running_loop()
        if self._loop is not running_loop:
            self._queue = asyncio.Queue()
            self._loop = running_loop
        if getattr(self._executor, "_shutdown", False):
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

    async def enqueue(self, task_data: dict) -> None:
        """Add a PDF processing job to the internal queue."""
        self.ensure_active_loop()
        await self._queue.put(task_data)

    async def worker_loop(self) -> None:
        """Infinite async loop consuming jobs from the queue."""
        from app.database import get_db_context
        from app.logger import log_event
        from app.tasks import update_task_status

        self.ensure_active_loop()
        loop = asyncio.get_running_loop()

        while True:
            try:
                task_data = await self._queue.get()
            except asyncio.CancelledError:
                raise
            except Exception as get_err:
                log_event("system", "ERROR", f"TaskQueue alma hatası: {get_err}")
                await asyncio.sleep(0.1)
                continue

            task_id = task_data.get("task_id") if isinstance(task_data, dict) else None
            tmp_path = task_data.get("tmp_path") if isinstance(task_data, dict) else None

            if not task_id or not isinstance(task_data, dict):
                log_event(
                    LOG_CATEGORY_UPLOAD, "ERROR", f"Geçersiz kuyruk görevi atlandı: {task_data}"
                )
                self._queue.task_done()
                continue

            try:
                # ── Phase 1: CPU-heavy work in background thread pool ────
                fn_low = str(task_data.get("filename") or "").lower()
                fmt_label = (
                    "EPUB"
                    if fn_low.endswith(".epub")
                    else ("Metin" if fn_low.endswith(".txt") else "PDF")
                )
                update_task_status(
                    task_id,
                    STATUS_PROCESSING,
                    15,
                    f"{fmt_label} metni okunuyor ve analiz için hazırlanıyor: {task_data['filename']}",
                    log_state="INFO",
                )

                result = await loop.run_in_executor(
                    self._executor,
                    _process_pdf_in_worker,
                    task_id,
                    task_data["tmp_path"],
                    task_data["filename"],
                    task_data["file_hash"],
                    task_data["provider"],
                    task_data["api_key"],
                    task_data["config"],
                    task_data["model_name"],
                    task_data["base_url"],
                )

                data = result["data"]
                final_path = result["final_path"]

                # ── Phase 2: Database write & chunk indexing ─────────────
                async with get_db_context() as bg_db:
                    book_entry = await _save_book_and_index_chunks(
                        bg_db=bg_db,
                        task_id=task_id,
                        task_data=task_data,
                        final_path=final_path,
                        data=data,
                        result=result,
                    )

                # ── Phase 3: Finalise & notify ───────────────────────────
                await _notify_task_completion(
                    task_id=task_id,
                    task_data=task_data,
                    final_path=final_path,
                    data=data,
                    book_entry=book_entry,
                )

            except Exception as e:
                log_event(LOG_CATEGORY_UPLOAD, "ERROR", f"PDF processing error: {e}")
                update_task_status(
                    task_id, STATUS_ERROR, 100, f"Hata oluştu: {str(e)}", log_state="error"
                )
            finally:
                await _cleanup_temp_file_safely(tmp_path)
                self._queue.task_done()

    def shutdown(self, wait: bool = True, cancel_futures: bool = True) -> None:
        """Gracefully shut down the thread pool."""
        try:
            self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
        except TypeError:
            self._executor.shutdown(wait=wait)
