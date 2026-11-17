"""Chat and workspace AI assistant endpoints router."""

import asyncio
import logging
import os
import sqlite3
import time

from fastapi import APIRouter, Depends, Header, Request

from app.auth import _ensure_authorized
from app.config import is_real_api_key, load_config, resolve_ai_credentials
from app.constants import (
    CHAT_CONTEXT_MAX_CHARS,
    DEFAULT_GEMINI_MODEL,
    MAX_NATIVE_PDF_BYTES,
)
from app.database import DatabaseManager
from app.dependencies import get_db
from app.logger import log_event
from app.models import ChatRequest
from app.prompts import (
    build_book_chat_prompt,
    build_book_system_instruction,
    build_catalog_system_instruction,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

EXT_FULL_TXT = ".full.txt"
EXT_TXT = ".txt"
LOG_CAT_AI_CHAT = "ai_chat"
PROVIDER_GEMINI = "gemini"

# Chat Context Cache (Library Profile)
_chat_cache = {"ts": 0, "data": ""}
_chat_cache_lock = asyncio.Lock()
_CHAT_CACHE_TTL = 300  # 5 minutes for stats is enough

# Guardrails for Gemini native-PDF chat mode
_GEMMA_NATIVE_PDF_MAX_CHARS = int(os.environ.get("GEMMA_NATIVE_PDF_MAX_CHARS", "600000"))
_MAX_NATIVE_PDF_BYTES = MAX_NATIVE_PDF_BYTES


def _estimate_tokens_from_chars(char_count: int) -> int:
    """Rough token estimate used only for safety logging and guardrails."""
    return max(1, char_count // 4)


def _read_text_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_text_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _get_cached_full_text(pdf_path: str) -> str:
    """Return cached full-text content for a book if available."""
    for suffix in (EXT_FULL_TXT, EXT_TXT):
        txt_path = f"{pdf_path}{suffix}"
        if os.path.exists(txt_path):
            try:
                content = _read_text_file(txt_path)
                if content:
                    return content
            except (OSError, UnicodeDecodeError):
                continue
    return ""


def _get_cached_full_text_char_count(pdf_path: str) -> int:
    """Return cached full-text character count for a book if available."""
    return len(_get_cached_full_text(pdf_path))


def _should_upload_native_pdf(pdf_path: str, provider: str = PROVIDER_GEMINI) -> tuple[bool, str]:
    """Verify if a PDF qualifies for direct Gemini Native PDF upload without context overflow or network timeout."""
    if not os.path.exists(pdf_path):
        return False, "PDF dosyası bulunamadı."

    # 1. Physical file size check
    try:
        size_bytes = os.path.getsize(pdf_path)
        if size_bytes > _MAX_NATIVE_PDF_BYTES:
            size_mb = size_bytes // (1024 * 1024)
            return (
                False,
                f"PDF boyutu ({size_mb} MB) doğrudan upload sınırını (200 MB) aşıyor.",
            )
    except OSError as e:
        logger.debug("Could not get PDF file size for %s: %s", pdf_path, e)

    # 2. Text character count check
    if provider != PROVIDER_GEMINI:
        char_count = _get_cached_full_text_char_count(pdf_path)
        if char_count > _GEMMA_NATIVE_PDF_MAX_CHARS:
            return (
                False,
                f"Kitap metin uzunluğu ({char_count:,} karakter) modelin bağlam sınırını aşıyor.",
            )

    return True, ""


def _looks_like_context_overflow_error(response_text: str) -> bool:
    """Detect token/context overflow-style provider errors from text payload."""
    if not response_text:
        return False
    lowered = response_text.lower()
    if "error" not in lowered:
        return False
    keywords = [
        "input token count",
        "exceeds the maximum",
        "maximum number of tokens",
        "context",
        "too long",
    ]
    return any(k in lowered for k in keywords)


async def _preinit_gemini_session(
    file_hash: str,
    dosya_yolu: str,
    db: DatabaseManager,
    http_request: Request,
) -> bool:
    """Pre-initialize Gemini session if API key is present."""
    from app.services.session_manager import book_session_manager

    cfg = load_config()
    _, api_key, model_name, _ = resolve_ai_credentials(
        provider=http_request.headers.get("x-ai-provider"),
        api_key=http_request.headers.get("x-ai-key"),
        model=http_request.headers.get("x-ai-model-name") or http_request.headers.get("x-ai-model"),
        base_url=http_request.headers.get("x-ai-base-url"),
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )
    if not (api_key and not api_key.startswith("••") and dosya_yolu and os.path.exists(dosya_yolu)):
        return False

    try:
        async with book_session_manager.lock_for(file_hash):
            session = book_session_manager.get_session(file_hash)
            if not session:
                cursor = await db.conn.execute(
                    "SELECT kitap_adi, yazar FROM kitaplar WHERE dosya_hash = ?",
                    (file_hash,),
                )
                b_info = await cursor.fetchone()
                k_name = b_info[0] if b_info else "Kitap"
                k_auth = b_info[1] if b_info else ""
                sys_inst = f"Sen, kullanıcının okumakta olduğu '{k_name}' (Yazar: {k_auth}) kitabının tüm içeriğine sahip, yardımcı ve akıllı bir yapay zeka asistanısın."
                await asyncio.to_thread(
                    book_session_manager.get_or_create_session,
                    book_hash=file_hash,
                    pdf_path=dosya_yolu,
                    model_name=model_name or DEFAULT_GEMINI_MODEL,
                    system_instruction=sys_inst,
                    api_key=api_key,
                )
        return True
    except Exception as sess_err:
        log_event(
            LOG_CAT_AI_CHAT,
            "WARNING",
            f"Workspace önceden oturum başlatma hatası: {sess_err}",
            file_hash=file_hash,
        )
        return False


@router.post("/workspace/load-book/{file_hash}")
async def workspace_load_book(
    file_hash: str, http_request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Pre-load and cache the full text of a book for deep AI context."""
    _ensure_authorized(http_request)
    try:
        row = await db.get_book_path(file_hash)
        if not row:
            return {"success": False, "error": "Kitap bulunamadı."}

        dosya_yolu, _ = row
        txt_path = dosya_yolu + EXT_FULL_TXT
        full_text = ""

        if os.path.exists(txt_path):
            full_text = await asyncio.to_thread(_read_text_file, txt_path)
        elif not os.path.exists(dosya_yolu):
            return {"success": False, "error": "PDF dosyası bulunamadı."}
        else:
            from app.pdf import extract_text_from_pdf

            full_text = await asyncio.to_thread(extract_text_from_pdf, dosya_yolu, max_pages=0)
            if full_text:
                try:
                    await asyncio.to_thread(_write_text_file, txt_path, full_text)
                except Exception as e:
                    logger.debug("Failed to write extracted text to cache %s: %s", txt_path, e)

        if not full_text or len(full_text.strip()) < 50:
            return {"success": False, "error": "Kitaptan yeterli metin çıkarılamadı."}

        char_count = len(full_text)

        has_session = await _preinit_gemini_session(
            file_hash=file_hash,
            dosya_yolu=dosya_yolu,
            db=db,
            http_request=http_request,
        )

        log_event(
            LOG_CAT_AI_CHAT,
            "INFO",
            f"Workspace: Kitap metni önbelleğe alındı ({char_count} karakter).",
            file_hash=file_hash,
        )
        return {"success": True, "char_count": char_count, "session_ready": has_session}

    except Exception as e:
        log_event(
            LOG_CAT_AI_CHAT,
            "ERROR",
            f"Workspace kitap yükleme hatası: {e}",
            file_hash=file_hash,
        )
        return {"success": False, "error": str(e)}


@router.get("/workspace/chat-history/{file_hash}")
async def workspace_chat_history(file_hash: str, http_request: Request) -> dict:
    """Retrieve in-memory chat history for a specific book workspace."""
    _ensure_authorized(http_request)
    from app.services.session_manager import book_session_manager

    history = book_session_manager.get_history(file_hash)
    has_session = book_session_manager.get_session(file_hash) is not None
    return {"success": True, "history": history, "has_active_session": has_session}


@router.post("/workspace/clear-chat/{file_hash}")
async def workspace_clear_chat(file_hash: str, http_request: Request) -> dict:
    """Clear in-memory chat session and history for a specific book."""
    _ensure_authorized(http_request)
    from app.services.session_manager import book_session_manager

    cleared = book_session_manager.clear_session(file_hash)
    return {"success": True, "cleared": cleared}


async def _resolve_agentic_intent(db: DatabaseManager, message: str) -> tuple[str | None, str]:
    """Detect agentic listing intent and retrieve corresponding database records."""
    msg_lower = message.lower()
    intent = None
    if any(
        k in msg_lower
        for k in ["tüm yazarlar", "hangi yazarlar", "yazar listesi", "bütün yazarlar"]
    ):
        intent = "list_authors"
    elif any(
        k in msg_lower
        for k in [
            "tüm kategoriler",
            "hangi kategoriler",
            "kategori listesi",
            "bütün kategoriler",
        ]
    ):
        intent = "list_categories"

    if not intent:
        return None, ""

    try:
        if intent == "list_authors":
            items = await db.get_distinct_values("yazar")
            agent_data = ", ".join(items) if items else "Hiç yazar bulunamadı."
        else:
            items = await db.get_distinct_values("kategori")
            agent_data = ", ".join(items) if items else "Hiç kategori bulunamadı."
        rag_context = (
            f"SİSTEM VERİTABANI YANITI: Kullanıcının kütüphanesindeki kayıtlı "
            f"{'yazarlar' if intent == 'list_authors' else 'kategoriler'} şunlardır: {agent_data}. "
            f"Lütfen bu veriyi kullanarak kullanıcıya doğal ve samimi bir dille yanıt ver.\n"
        )
        return intent, rag_context
    except sqlite3.Error as agent_err:
        log_event("ai_chat", "ERROR", f"Agentic Routing veritabanı sorgu hatası: {agent_err}")
    except Exception as agent_err:
        log_event(
            "ai_chat",
            "ERROR",
            f"Agentic Routing çalıştırılırken beklenmedik hata: {agent_err}",
        )
    return None, ""


async def _build_catalog_context(db: DatabaseManager) -> str:
    """Fetch all book catalog titles, authors, categories, summaries, and keywords."""
    try:
        cursor = await db.conn.execute(
            "SELECT kitap_adi, yazar, kategori, ozet, anahtar_kelimeler FROM kitaplar ORDER BY sira_numarasi ASC, id DESC LIMIT 300"
        )
        books = await cursor.fetchall()
        if not books:
            return "Kütüphanede henüz kayıtlı kitap bulunmamaktadır.\n\n"

        catalog_lines = ["KÜTÜPHANE KATALOĞU (Tüm Kitaplar ve Özetleri):"]
        for b_title, b_author, b_cat, b_summary, b_keys in books:
            b_str = f"• Kitap: {b_title or 'İsimsiz'} | Yazar: {b_author or 'Bilinmiyor'} | Kategori: {b_cat or 'Genel'}"
            if b_summary:
                b_str += f"\n  Özet: {b_summary.strip()}"
            if b_keys:
                b_str += f"\n  Anahtar Kelimeler: {b_keys.strip()}"
            catalog_lines.append(b_str)
        log_event(
            "ai_chat",
            "INFO",
            f"Genel sohbet: {len(books)} kitabın katalog özeti bağlama eklendi.",
        )
        return "\n".join(catalog_lines) + "\n\n"
    except Exception as cat_err:
        log_event("ai_chat", "WARNING", f"Genel katalog özeti yüklenirken hata: {cat_err}")
        return ""


async def _get_hybrid_passages(db: DatabaseManager, target_book_hash: str, user_query: str) -> str:
    """Retrieve hybrid semantic passages for a book query."""
    if not user_query or not user_query.strip():
        return ""
    try:
        from app.services.hybrid_search import hybrid_search_engine

        passages = await hybrid_search_engine.hybrid_search(
            db, user_query, file_hash=target_book_hash, limit=6
        )
        if not passages:
            return ""
        lines = [
            "--- KULLANICININ SORUSUNA İLİŞKİN KİTAPTAN BULUNAN EN İLGİLİ SAYFA VE PASAJLAR ---",
            "Aşağıdaki pasajları esas alarak yanıt ver. Bilgileri aktarırken ilgili cümlenin sonuna mutlaka [Sayfa X] (örn: [Sayfa 42]) şeklinde kaynak sayfa numarasını iliştir:",
        ]
        for p in passages:
            lines.append(f"[Sayfa {p['sayfa_no']}]: {p['metin']}")
        lines.append("--- İLGİLİ PASAJLAR SONU ---\n")
        log_event(
            LOG_CAT_AI_CHAT,
            "INFO",
            f"Hibrit RAG: {len(passages)} adet ilgili sayfa pasajı bağlama eklendi.",
        )
        return "\n".join(lines) + "\n"
    except Exception as rag_err:
        log_event(LOG_CAT_AI_CHAT, "WARNING", f"Hibrit RAG pasaj araması uyarısı: {rag_err}")
        return ""


async def _load_book_text_or_pdf(
    k_yolu: str, target_book_hash: str, provider: str, k_adi: str
) -> tuple[str, str | None]:
    """Decide between native PDF upload or text extraction."""
    if not k_yolu or not os.path.exists(k_yolu):
        return "", None

    import sys

    app_main = sys.modules.get("app.main")
    check_pdf_fn = (
        getattr(app_main, "_should_upload_native_pdf", _should_upload_native_pdf)
        if app_main
        else _should_upload_native_pdf
    )
    can_upload_pdf, no_upload_reason = check_pdf_fn(k_yolu, provider=provider)

    if provider == PROVIDER_GEMINI and can_upload_pdf:
        log_event(
            LOG_CAT_AI_CHAT,
            "INFO",
            f"Kitap doğrudan PDF olarak Gemini API'ye yüklenecek: {k_yolu}",
            file_hash=target_book_hash,
        )
        return "", k_yolu

    if provider == PROVIDER_GEMINI and not can_upload_pdf:
        log_event(
            LOG_CAT_AI_CHAT,
            "WARNING",
            f"Gemini tam-PDF modu devre dışı bırakıldı, metin tabanlı moda geçiliyor: {no_upload_reason}",
            file_hash=target_book_hash,
        )

    full_text = _get_cached_full_text(k_yolu)
    if not full_text:
        lower_p = k_yolu.lower()
        if lower_p.endswith(".epub"):
            from app.epub import extract_text_from_epub

            full_text = await asyncio.to_thread(extract_text_from_epub, k_yolu, max_chars=250000)
        elif lower_p.endswith(".txt"):
            from app.epub import extract_text_from_txt

            full_text = await asyncio.to_thread(extract_text_from_txt, k_yolu, max_chars=250000)
        else:
            from app.pdf import extract_text_from_pdf

            full_text = await asyncio.to_thread(extract_text_from_pdf, k_yolu, max_pages=0)
        for sfx in (EXT_FULL_TXT, EXT_TXT):
            try:
                await asyncio.to_thread(_write_text_file, k_yolu + sfx, full_text)
            except OSError as e:
                logger.debug("Could not write full text cache for %s: %s", k_yolu, e)

    if not full_text:
        return "", None

    loaded_len = len(full_text)
    if len(full_text) > CHAT_CONTEXT_MAX_CHARS:
        full_text = (
            full_text[:CHAT_CONTEXT_MAX_CHARS]
            + f"\n\n[Sistem Notu: Kitap çok uzun olduğu için ilk {CHAT_CONTEXT_MAX_CHARS:,} karakteri bağlama alınmıştır.]"
        )
    log_event(
        LOG_CAT_AI_CHAT,
        "INFO",
        f"Tam kitap metni LLM bağlamına yüklendi ({loaded_len} karakter).",
    )
    return (
        f"--- AŞAĞIDA '{k_adi}' KİTABININ TAM METNİ YER ALMAKTADIR ---\n{full_text}\n--- TAM METİN SONU ---\n\n",
        None,
    )


async def _build_target_book_context(
    db: DatabaseManager,
    target_book_hash: str,
    provider: str,
    user_query: str = "",
) -> tuple[dict, str, str | None]:
    """Retrieve metadata, full text, and notes for a specific target book."""
    book_meta = {"title": "", "author": "", "summary": "", "path": ""}
    rag_context = ""
    pdf_to_upload = None

    try:
        cursor = await db.conn.execute(
            "SELECT kitap_adi, yazar, ozet, dosya_yolu FROM kitaplar WHERE dosya_hash = ?",
            (target_book_hash,),
        )
        book_details = await cursor.fetchone()
        if not book_details:
            return book_meta, rag_context, pdf_to_upload

        k_adi, k_yazar, k_ozet, raw_yolu = book_details
        from app.constants import LIBRARY_ROOT
        from app.utils import resolve_portable_book_path

        k_yolu = resolve_portable_book_path(raw_yolu, LIBRARY_ROOT)
        book_meta = {
            "title": k_adi or "",
            "author": k_yazar or "",
            "summary": k_ozet or "",
            "path": k_yolu or "",
            "supplemental_context": "",
        }
        rag_context += f"SİSTEM BİLGİSİ: Kullanıcı şu anda '{k_adi}' (Yazar: {k_yazar}) kitabını okuyor/inceliyor.\nKitap Özeti: {k_ozet}\n\n"

        # Hybrid RAG Semantic Retrieval for targeted query
        hybrid_passages = await _get_hybrid_passages(db, target_book_hash, user_query)
        rag_context += hybrid_passages

        text_ctx, pdf_path = await _load_book_text_or_pdf(k_yolu, target_book_hash, provider, k_adi)
        rag_context += text_ctx
        if pdf_path:
            pdf_to_upload = pdf_path

        user_notes_context = ""
        try:
            user_notes_context = await db.get_book_notes_for_ai(target_book_hash)
            if user_notes_context:
                rag_context += user_notes_context
                log_event(
                    LOG_CAT_AI_CHAT,
                    "INFO",
                    "Kullanıcı okuma notları ve alıntıları LLM bağlamına eklendi.",
                    file_hash=target_book_hash,
                )
        except Exception as notes_err:
            log_event(
                LOG_CAT_AI_CHAT,
                "WARNING",
                f"Kullanıcı notları bağlama eklenirken hata: {notes_err}",
            )

        supplemental_parts = [p for p in (hybrid_passages.strip(), user_notes_context.strip()) if p]
        if supplemental_parts:
            book_meta["supplemental_context"] = "\n\n".join(supplemental_parts)

    except Exception as book_err:
        log_event(LOG_CAT_AI_CHAT, "WARNING", f"Workspace kitap metni yüklenirken hata: {book_err}")

    return book_meta, rag_context, pdf_to_upload


async def _get_cached_library_stats(db: DatabaseManager) -> str:
    """Retrieve or refresh cached library profile statistics."""
    async with _chat_cache_lock:
        now = time.time()
        if now - float(_chat_cache["ts"]) > _CHAT_CACHE_TTL:
            try:
                _chat_cache["data"] = await db.get_chat_stats()
            except sqlite3.Error as db_err:
                log_event(
                    "ai_chat",
                    "ERROR",
                    f"Chat istatistik önbelleği güncellenirken veritabanı hatası oluştu: {db_err}",
                )
                _chat_cache["data"] = "Kütüphane istatistikleri şu an alınamadı."
            except Exception as e:
                log_event(
                    "ai_chat",
                    "ERROR",
                    f"Chat istatistik önbelleği güncellenirken beklenmedik hata oluştu: {e}",
                )
                _chat_cache["data"] = "Kütüphane istatistikleri şu an alınamadı."
            _chat_cache["ts"] = now
        return _chat_cache["data"]


async def _execute_chat_llm(
    request: ChatRequest,
    provider: str,
    api_key: str,
    model_name: str | None,
    base_url: str | None,
    system_instruction: str,
    prompt: str,
    rag_context: str,
    pdf_to_upload: str | None,
    book_meta: dict,
    cfg: dict,
) -> tuple[str, str]:
    """Generate AI response with session support and overflow fallback."""
    k_adi = book_meta.get("title", "")
    k_yazar = book_meta.get("author", "")
    full_book_mode_notice = ""

    if (
        request.target_book_hash
        and provider == PROVIDER_GEMINI
        and pdf_to_upload
        and os.path.exists(pdf_to_upload)
    ):
        from app.services.session_manager import book_session_manager

        async with book_session_manager.lock_for(request.target_book_hash):
            book_session = await asyncio.to_thread(
                book_session_manager.get_or_create_session,
                book_hash=request.target_book_hash,
                pdf_path=pdf_to_upload,
                model_name=model_name,
                system_instruction=system_instruction
                or f"Sen '{k_adi or 'Kitap'}' kitabını derinlemesine bilen uzman bir asistansın.",
                api_key=api_key,
            )
            supplemental_ctx = str(book_meta.get("supplemental_context") or "")
            response_text = await asyncio.to_thread(
                book_session.send_user_message,
                request.message,
                supplemental_ctx,
            )
    else:
        from app.ai_router import generate_ai_response

        google_search_grounding = bool(cfg.get("google_search_grounding", False))
        response_text = await asyncio.to_thread(
            generate_ai_response,
            prompt=prompt,
            provider=provider,
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            system_instruction=system_instruction,
            google_search_grounding=google_search_grounding,
            pdf_path=pdf_to_upload,
        )

    if pdf_to_upload and _looks_like_context_overflow_error(response_text):
        log_event(
            LOG_CAT_AI_CHAT,
            "WARNING",
            "Gemini tam-PDF yanıtı context limitine takıldı; alıntı tabanlı moda geri dönülüyor.",
            file_hash=request.target_book_hash,
            model=model_name,
        )
        fallback_system_instruction = (
            f"Sen, kullanıcının okumakta olduğu '{k_adi}' (Yazar: {k_yazar}) kitabından alınan alıntılara sahip, "
            "yardımcı ve akıllı bir yapay zeka asistanısın."
            if k_adi
            else system_instruction
        )
        fallback_prompt = (
            f"Kitaptan alınan ilgili alıntılar aşağıdadır:\n\n--- ALINTILAR ---\n\n{rag_context}\n\n"
            f"--- ALINTILAR SONU ---\n\nKullanıcının Sorusu: {request.message}\n\n"
            "Lütfen bu soruyu sağlanan alıntılara dayanarak doğrudan ve doğal bir şekilde Türkçe olarak yanıtla:"
        )

        from app.ai_router import generate_ai_response

        response_text = await asyncio.to_thread(
            generate_ai_response,
            prompt=fallback_prompt,
            provider=provider,
            api_key=api_key,
            model=model_name,
            base_url=base_url,
            system_instruction=fallback_system_instruction,
            google_search_grounding=bool(cfg.get("google_search_grounding", False)),
            pdf_path=None,
        )
        full_book_mode_notice = "Tam kitap modu bu mesaj için bağlam sınırına takıldı; yanıt alıntı tabanlı güvenli modla üretildi."

    return response_text, full_book_mode_notice


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    http_request: Request,
    x_ai_provider: str | None = Header(None),
    x_ai_key: str | None = Header(None),
    x_ai_model: str | None = Header(None, alias="X-AI-Model"),
    x_ai_model_name: str | None = Header(None, alias="X-AI-Model-Name"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-Url"),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Chat endpoint with RAG supporting multiple AI providers via headers."""
    _ensure_authorized(http_request)
    cfg = load_config()
    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=x_ai_provider,
        api_key=x_ai_key,
        model=x_ai_model_name or x_ai_model,
        base_url=x_ai_base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    if not api_key and provider not in ["ollama", "lmstudio"]:
        return {"response": "Lütfen ayarlardan API anahtarınızı girin."}

    # 1. Check for agentic listing intents (authors, categories)
    intent, rag_context = await _resolve_agentic_intent(db, request.message)

    # 2. Assemble context based on workspace book or library catalog
    pdf_to_upload = None
    book_meta = {}
    if not intent:
        if request.target_book_hash:
            book_meta, book_rag, pdf_to_upload = await _build_target_book_context(
                db, request.target_book_hash, provider, user_query=request.message
            )
            rag_context += book_rag
        else:
            rag_context += await _build_catalog_context(db)

    library_profile = await _get_cached_library_stats(db)

    # 3. Formulate system instruction and prompt using prompts module
    k_adi = book_meta.get("title", "")
    k_yazar = book_meta.get("author", "")

    if request.target_book_hash and k_adi:
        is_full = bool(request.load_full_book)
        system_instruction = build_book_system_instruction(k_adi, k_yazar, is_full_text=is_full)
        prompt = build_book_chat_prompt(
            user_message=request.message,
            rag_context=rag_context,
            is_native_gemini=(provider == PROVIDER_GEMINI),
            is_full_text=is_full,
        )
    else:
        system_instruction = build_catalog_system_instruction()
        prompt = f"[KULLANICININ KÜTÜPHANE KATALOĞU VE ÖZETLERİ]:\n{rag_context}\n\n[KÜTÜPHANE GENEL İSTATİSTİKLERİ]:\n{library_profile}\n\nKullanıcının Sorusu / Talebi:\n{request.message}\n\nBu talebi, kütüphanenin içeriğini ve engin kitap kültürünü harmanlayarak doğrudan, samimi ve doyurucu bir şekilde yanıtla:"

    # 4. Generate AI response with session support and overflow fallback
    try:
        response_text, full_book_mode_notice = await _execute_chat_llm(
            request=request,
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            system_instruction=system_instruction,
            prompt=prompt,
            rag_context=rag_context,
            pdf_to_upload=pdf_to_upload,
            book_meta=book_meta,
            cfg=cfg,
        )

        payload = {"response": response_text}
        if full_book_mode_notice:
            payload["mode_notice"] = full_book_mode_notice
        return payload

    except Exception as e:
        err_type = "AI API Bağlantı Hatası"
        try:
            import httpx

            if not isinstance(e, httpx.HTTPError):
                err_type = "Sistem Yanıt Hatası"
        except ImportError:
            err_type = "Sistem/API Hatası"
        log_event(LOG_CAT_AI_CHAT, "ERROR", f"AI chat hatası ({provider}) [{err_type}]: {e}")
        return {"response": "Üzgünüm, şu an yanıt veremiyorum."}
