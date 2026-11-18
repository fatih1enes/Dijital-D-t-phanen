"""Books, upload, reading progress and annotations endpoints router."""

import asyncio
import glob
import os
import re
import shutil
import tempfile
import time
import uuid
from typing import Any
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi_cache import FastAPICache
from PIL import Image

from app.auth import _ensure_authorized
from app.config import is_real_api_key, load_config, resolve_ai_credentials
from app.constants import (
    CHUNK_READ_SIZE,
    DEFAULT_MAX_PAGES,
    LIBRARY_ROOT,
    MAX_COVER_BYTES,
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_BYTES,
    THUMBNAILS_DIR,
)
from app.database import DatabaseManager
from app.dependencies import get_db
from app.logger import log_event, notify_ws
from app.models import (
    AnnotationBatchRequest,
    AnnotationCreateRequest,
    BookmarkToggleRequest,
    BookOrderRequest,
    BookUpdateRequest,
    SaveProgressRequest,
)
from app.pdf import prepare_cover_image
from app.utils import (
    get_file_hash_from_path,
    is_path_within,
    looks_like_supported_document,
    validate_file_hash,
)

router = APIRouter(prefix="/api", tags=["books"])

EXT_FULL_TXT = ".full.txt"
EXT_EPUB = ".epub"
EXT_PDF = ".pdf"
EXT_TXT = ".txt"
CACHE_NAMESPACE_BOOKS = "books"
CACHE_NAMESPACE_STATS = "stats"
WS_EVENT_LIBRARY_UPDATE = "library_update"
LOG_CAT_FILESYSTEM = "filesystem"
LOG_CAT_PROCESSING = "processing"
LOG_CAT_UPLOAD = "upload"
STATUS_SUCCESS = "success"
ERR_BOOK_NOT_FOUND = "Book not found"


def _safe_remove_temp(path: str, msg: str) -> None:
    """Safely remove a temporary file and log if an error occurs."""
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError as e:
            log_event(LOG_CAT_UPLOAD, "DEBUG", f"{msg}: {e}", path=path)


def _validate_upload_filename(filename: str) -> None:
    """Validate that filename is not a derivative or cache file."""
    base_name = filename.lower()
    if (
        base_name.endswith((EXT_FULL_TXT, ".pdf.txt", ".epub.txt", ".txt.txt", ".cache.txt"))
        or ".pdf." in base_name
        or ".epub." in base_name
        or ".txt." in base_name
    ):
        raise HTTPException(
            status_code=400,
            detail="Önbellek veya türetilmiş metin dosyaları kitap olarak yüklenemez.",
        )


async def read_limited_upload(upload: UploadFile, max_bytes: int, label: str) -> bytes:
    """Read an uploaded file in chunks up to max_bytes to prevent memory exhaustion (DoS)."""
    total = 0
    chunks = []
    while True:
        chunk = await upload.read(CHUNK_READ_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            limit_mb = max_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"{label} boyutu çok büyük (Maksimum {limit_mb} MB).",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _open_temp_file(suffix: str) -> Any:
    """Open a temporary file synchronously outside of async context."""
    return tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb")


async def stream_upload_to_temp_file(
    upload: UploadFile, max_bytes: int, label: str, suffix: str = ""
) -> tuple[str, str, bytes, int]:
    """Stream uploaded file directly to disk while computing hash and checking limits (DoS safe)."""
    import hashlib

    hasher = hashlib.sha256()
    total = 0
    first_chunk = b""

    with _open_temp_file(suffix) as tmp:
        tmp_path = tmp.name
        try:
            while True:
                chunk = await upload.read(CHUNK_READ_SIZE)
                if not chunk:
                    break
                if not first_chunk:
                    first_chunk = chunk
                total += len(chunk)
                if total > max_bytes:
                    limit_mb = max_bytes // (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"{label} boyutu çok büyük (Maksimum {limit_mb} MB).",
                    )
                tmp.write(chunk)
                hasher.update(chunk)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError as e:
                    log_event(
                        LOG_CAT_UPLOAD,
                        "DEBUG",
                        f"Temp upload dosyası temizlenirken hata: {e}",
                        path=tmp_path,
                    )
            raise

    return tmp_path, hasher.hexdigest(), first_chunk, total


@router.get("/books")
async def get_books(
    request: Request,
    response: Response,
    page: int = 1,
    limit: int = 50,
    category: str | None = None,
    search: str | None = None,
    favorite: bool | None = None,
    collection_id: int | None = None,
    sort: str | None = None,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Get books with pagination and optional category, search, favorite, collection, and sort filters."""
    _ensure_authorized(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    safe_page = max(1, page)
    safe_limit = max(1, min(1000, limit))
    offset = (safe_page - 1) * safe_limit
    return await db.get_all_books(
        limit=safe_limit,
        offset=offset,
        category=category,
        search=search,
        favorite=favorite,
        collection_id=collection_id,
        sort=sort,
    )


@router.get("/search/deep")
async def deep_search(
    request: Request,
    q: str = "",
    limit: int = 30,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Global Deep Search across all pages and chunks in the library."""
    _ensure_authorized(request)
    from app.services.hybrid_search import hybrid_search_engine

    clean_q = str(q or "").strip()
    if not clean_q:
        return {"query": "", "total_matches": 0, "results": []}
    safe_limit = max(1, min(100, limit))
    results = await hybrid_search_engine.deep_search_pages(db, query=clean_q, limit=safe_limit)
    return {"query": clean_q, "total_matches": len(results), "results": results}


@router.put("/books/order")
async def update_book_order(
    request: Request, payload: BookOrderRequest, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Update custom book order."""
    _ensure_authorized(request)
    await db.save_book_order(payload.order)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    notify_ws(WS_EVENT_LIBRARY_UPDATE, {})
    return {"status": STATUS_SUCCESS}


@router.post(
    "/upload",
    responses={
        400: {"description": "Geçersiz dosya formatı, türetilmiş dosya veya eksik API anahtarı"},
        413: {"description": "Dosya boyutu çok büyük"},
    },
)
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    x_ai_provider: str | None = Header(None, alias="X-AI-Provider"),
    x_ai_key: str | None = Header(None, alias="X-AI-Key"),
    x_ai_model: str | None = Header(None, alias="X-AI-Model"),
    x_ai_model_name: str | None = Header(None, alias="X-AI-Model-Name"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-URL"),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Upload PDF endpoint supporting multiple AI providers via headers."""
    _ensure_authorized(request)
    cfg = load_config()

    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=x_ai_provider,
        api_key=x_ai_key,
        model=x_ai_model_name or x_ai_model,
        base_url=x_ai_base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    is_local = provider in ("ollama", "lmstudio")
    if not api_key and not is_local:
        raise HTTPException(
            status_code=400,
            detail="AI API Key is required (X-AI-Key header or saved settings)",
        )

    _validate_upload_filename(file.filename or "")

    _, ext = os.path.splitext(file.filename or "")
    ext_lower = ext.lower()
    safe_suffix = ext_lower if ext_lower in (EXT_PDF, EXT_EPUB, EXT_TXT) else EXT_PDF

    tmp_path, file_hash, first_chunk, total_bytes = await stream_upload_to_temp_file(
        file, MAX_UPLOAD_BYTES, "Belge dosyası", suffix=safe_suffix
    )

    is_valid, _ = looks_like_supported_document(first_chunk, file.filename or "")
    if not is_valid:
        _safe_remove_temp(tmp_path, "Geçersiz dosya temp silme hatası")
        raise HTTPException(
            status_code=400,
            detail="Geçersiz dosya formatı. Sadece PDF, EPUB ve TXT dosyaları desteklenir.",
        )

    if await db.book_exists(file_hash):
        _safe_remove_temp(tmp_path, "Mevcut kitap temp silme hatası")
        log_event(
            LOG_CAT_UPLOAD,
            "INFO",
            f"Yüklenen kitap zaten kütüphanede mevcut: {file.filename}",
            file_hash=file_hash,
            filename=file.filename,
        )
        return {"status": "exists", "file_hash": file_hash}

    task_id = str(uuid.uuid4())
    task_entry = {
        "filename": file.filename,
        "status": "processing",
        "percentage": 5,
        "log_message": "Kuyrukta bekliyor...",
        "last_update": time.time(),
        "logs": [
            {
                "ts": time.time(),
                "message": "Dosya yüklendi, analiz kuyruğuna alındı...",
                "status": "processing",
                "state": "pending",
                "pct": 5,
            }
        ],
    }
    from app.tasks import register_task

    register_task(task_id, task_entry)

    log_event(
        "upload",
        "INFO",
        f"Yeni kitap yüklendi ve işleme kuyruğuna alındı: {file.filename}",
        task_id=task_id,
        filename=file.filename,
        size_bytes=total_bytes,
    )
    notify_ws("task", {"task_id": task_id, "task": task_entry})

    await request.app.state.task_queue.enqueue(
        {
            "task_id": task_id,
            "tmp_path": tmp_path,
            "filename": file.filename,
            "file_hash": file_hash,
            "provider": provider,
            "api_key": api_key,
            "config": cfg,
            "model_name": model_name,
            "base_url": base_url,
        }
    )

    return {"task_id": task_id, "status": "processing"}


def _is_ignorable_sync_file(file_path: str) -> bool:
    """Check if file should be skipped during library sync."""
    if "Kaldirilmis_PDFler" in file_path:
        return True
    base_name = os.path.basename(file_path).lower()
    if (
        base_name.endswith((EXT_FULL_TXT, ".pdf.txt", ".epub.txt", ".txt.txt", ".cache.txt"))
        or ".pdf." in base_name
        or ".epub." in base_name
        or ".txt." in base_name
    ):
        return True
    if base_name.endswith(EXT_TXT):
        stem = os.path.splitext(base_name)[0]
        dir_name = os.path.dirname(file_path)
        if any(
            os.path.exists(os.path.join(dir_name, f"{stem}{ext}")) for ext in (EXT_PDF, EXT_EPUB)
        ):
            return True
    return False


@router.post(
    "/books/sync",
    responses={400: {"description": "AI API Key is required to scan/process files."}},
)
async def sync_library(
    request: Request,
    x_ai_provider: str | None = Header(None, alias="X-AI-Provider"),
    x_ai_key: str | None = Header(None, alias="X-AI-Key"),
    x_ai_model: str | None = Header(None, alias="X-AI-Model"),
    x_ai_model_name: str | None = Header(None, alias="X-AI-Model-Name"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-URL"),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Sync library by scanning the LIBRARY_ROOT directory recursively for unregistered files."""
    _ensure_authorized(request)
    cfg = load_config()

    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=x_ai_provider,
        api_key=x_ai_key,
        model=x_ai_model_name or x_ai_model,
        base_url=x_ai_base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    is_local = provider in ("ollama", "lmstudio")
    if not api_key and not is_local:
        raise HTTPException(
            status_code=400,
            detail="AI API Key is required to scan/process files.",
        )

    watch_dir = str(cfg.get("watchfolder_path", "")).strip()
    watch_dir_valid = bool(watch_dir and os.path.isdir(watch_dir))

    def _scan_library_files() -> list[str]:
        from app.services.watchfolder_service import _get_scan_candidates, _is_file_readable

        scanned: list[str] = []
        seen_norm: set[str] = set()
        for ext in ("*.pdf", "*.epub", "*.txt"):
            pattern = os.path.join(LIBRARY_ROOT, "**", ext)
            for candidate in glob.glob(pattern, recursive=True):
                norm_p = os.path.normcase(os.path.realpath(os.path.abspath(candidate)))
                if norm_p not in seen_norm:
                    seen_norm.add(norm_p)
                    scanned.append(candidate)

        if watch_dir_valid and not is_path_within(LIBRARY_ROOT, watch_dir):
            for candidate in _get_scan_candidates(watch_dir):
                if not _is_file_readable(candidate):
                    continue
                norm_p = os.path.normcase(os.path.realpath(os.path.abspath(candidate)))
                if norm_p not in seen_norm:
                    seen_norm.add(norm_p)
                    scanned.append(candidate)

        return scanned

    scanned_files = await asyncio.to_thread(_scan_library_files)

    def _copy_to_temp(src_path: str, suffix: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
            shutil.copy2(src_path, tmp.name)
            return tmp.name

    # Pre-fetch existing normalized paths to skip redundant SHA-256 hashing of already-indexed files
    path_cur = await db.conn.execute("SELECT dosya_yolu FROM kitaplar WHERE dosya_yolu IS NOT NULL")
    existing_paths = {
        os.path.normcase(os.path.realpath(os.path.abspath(r[0])))
        for r in await path_cur.fetchall()
        if r[0]
    }

    from app.services.watchfolder_service import watchfolder_service
    from app.tasks import register_task

    enqueued_count = 0
    for file_path in scanned_files:
        if _is_ignorable_sync_file(file_path):
            continue

        norm_candidate = os.path.normcase(os.path.realpath(os.path.abspath(file_path)))
        if norm_candidate in existing_paths:
            continue

        try:
            file_hash = await asyncio.to_thread(get_file_hash_from_path, file_path)
            if await db.book_exists(file_hash):
                continue

            _, f_ext = os.path.splitext(file_path)
            tmp_path = await asyncio.to_thread(_copy_to_temp, file_path, f_ext.lower())

            filename = os.path.basename(file_path)
            task_id = str(uuid.uuid4())
            register_task(
                task_id,
                {
                    "filename": filename,
                    "status": "processing",
                    "percentage": 0,
                    "log_message": "Kuyrukta bekliyor...",
                    "last_update": time.time(),
                    "logs": [
                        {
                            "ts": time.time(),
                            "message": "Dosya tarama sonucu kuyruğa alındı...",
                            "status": "processing",
                            "state": "pending",
                            "pct": 0,
                        }
                    ],
                },
            )

            await request.app.state.task_queue.enqueue(
                {
                    "task_id": task_id,
                    "tmp_path": tmp_path,
                    "filename": filename,
                    "file_hash": file_hash,
                    "provider": provider,
                    "api_key": api_key,
                    "config": cfg,
                    "model_name": model_name,
                    "base_url": base_url,
                }
            )
            watchfolder_service._processed_hashes.add(file_hash)
            enqueued_count += 1
        except Exception as e:
            log_event(
                "system",
                "ERROR",
                f"Taranan belge dosyası '{file_path}' işlenirken hata: {e}",
            )

    return {
        "status": "success",
        "enqueued_count": enqueued_count,
        "watchfolder_scanned": watch_dir_valid,
        "watchfolder_path": watch_dir if watch_dir_valid else "",
    }


@router.delete(
    "/books/{file_hash}",
    responses={409: {"description": "Dosya başka bir işlem tarafından kullanılıyor"}},
)
async def delete_book(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Delete book endpoint."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    from app.services.session_manager import book_session_manager

    await asyncio.to_thread(book_session_manager.clear_session, file_hash)
    try:
        await db.delete_book(file_hash)
    except PermissionError as lock_err:
        raise HTTPException(
            status_code=409,
            detail="Kitap dosyası başka bir işlem tarafından kullanıldığı için şu an silinemiyor.",
        ) from lock_err
    from app.event_bus import BookDeletedEvent, event_bus

    await event_bus.publish(BookDeletedEvent(file_hash=file_hash))
    return {"status": "deleted"}


async def _extract_text_for_reanalysis(file_path: str, filename: str, max_pages: int) -> str:
    """Extract sample text from EPUB, TXT, or PDF for AI analysis."""
    from app.epub import extract_text_from_epub, extract_text_from_txt
    from app.pdf import extract_text_from_pdf

    lower_fn = filename.lower()
    if lower_fn.endswith(EXT_EPUB):
        return await asyncio.to_thread(extract_text_from_epub, file_path, max_chars=25000)
    if lower_fn.endswith(EXT_TXT):
        return await asyncio.to_thread(extract_text_from_txt, file_path, max_chars=25000)
    return await asyncio.to_thread(extract_text_from_pdf, file_path, max_pages=max_pages)


def _relocate_reanalyzed_file(ai_data: dict, file_path: str, filename: str, file_hash: str) -> None:
    """Move physical file to new category folder if category was updated."""
    new_cat = ai_data.get("kategori")
    if not new_cat or new_cat == "Bilinmeyen":
        return
    from app.utils import sanitize_dirname, sanitize_filename

    new_cat_dir = os.path.join(LIBRARY_ROOT, sanitize_dirname(new_cat))
    os.makedirs(new_cat_dir, exist_ok=True)
    new_file_path = os.path.join(new_cat_dir, sanitize_filename(filename))
    if (
        new_file_path != file_path
        and not os.path.exists(new_file_path)
        and os.path.exists(file_path)
    ):
        try:
            shutil.move(file_path, new_file_path)
            for sfx in (EXT_FULL_TXT, EXT_TXT):
                if os.path.exists(file_path + sfx):
                    shutil.move(file_path + sfx, new_file_path + sfx)
            ai_data["dosya_yolu"] = new_file_path
        except Exception as me:
            log_event(
                LOG_CAT_FILESYSTEM,
                "WARNING",
                f"Kitap yeni kategoriye taşınırken uyarı: {me}",
                file_hash=file_hash,
            )


@router.post(
    "/books/{file_hash}/reanalyze",
    responses={
        400: {"description": "Yapay zeka analizi için API anahtarı gereklidir"},
        404: {"description": "Kitap dosyası veritabanında veya diskte bulunamadı"},
        500: {"description": "Kitap yeniden analiz edilirken sunucu hatası"},
    },
)
async def reanalyze_book(
    file_hash: str,
    request: Request,
    x_ai_key: str | None = Header(None, alias="X-AI-Key"),
    x_ai_provider: str | None = Header(None, alias="X-AI-Provider"),
    x_ai_model: str | None = Header(None, alias="X-AI-Model"),
    x_ai_model_name: str | None = Header(None, alias="X-AI-Model-Name"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-Url"),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Re-analyze an existing book using AI."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)

    cfg = load_config()
    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=x_ai_provider,
        api_key=x_ai_key,
        model=x_ai_model_name or x_ai_model,
        base_url=x_ai_base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    is_local = provider in ("ollama", "lmstudio")
    if not api_key and not is_local:
        raise HTTPException(
            status_code=400,
            detail="Yapay zeka analizini çalıştırmak için API anahtarı gereklidir.",
        )

    # Get book file path
    res = await db.get_book_path(file_hash)
    if not res or not res[0]:
        raise HTTPException(status_code=404, detail="Kitap dosyası veritabanında bulunamadı.")
    file_path, filename = res

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fiziksel kitap dosyası diskte bulunamadı: {file_path}",
        )

    from app.task_queue import _analyze_pdf_standalone

    try:
        max_pages = cfg.get("max_pages", DEFAULT_MAX_PAGES)
        text_for_ai = await _extract_text_for_reanalysis(file_path, filename, max_pages)

        ai_data = await asyncio.to_thread(
            _analyze_pdf_standalone,
            filename=filename,
            text=text_for_ai,
            provider=provider,
            api_key=api_key,
            config=cfg,
            model_name=model_name,
            base_url=base_url,
        )

        if ai_data.get("kitap_adi") and not str(ai_data.get("ozet", "")).startswith(
            "Analiz başarısız"
        ):
            if isinstance(ai_data.get("anahtar_kelimeler"), list):
                ai_data["anahtar_kelimeler"] = ", ".join(map(str, ai_data["anahtar_kelimeler"]))

            _relocate_reanalyzed_file(ai_data, file_path, filename, file_hash)

            await db.update_book(file_hash, ai_data)
            await db._auto_clean_categories(file_hash)
            await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
            await FastAPICache.clear(namespace=CACHE_NAMESPACE_STATS)
            notify_ws(
                WS_EVENT_LIBRARY_UPDATE,
                {
                    "reason": "reanalyze_complete",
                    "file_hash": file_hash,
                    "data": ai_data,
                },
            )
            return {"status": STATUS_SUCCESS, "data": ai_data}

        return {
            "status": "error",
            "message": ai_data.get("ozet", "Analiz tamamlanamadı."),
            "data": ai_data,
        }
    except HTTPException:
        raise
    except Exception as err:
        log_event(
            "ai_analyze",
            "ERROR",
            f"Yeniden analiz sırasında hata: {err}",
            file_hash=file_hash,
        )
        raise HTTPException(
            status_code=500,
            detail="Kitap yeniden analiz edilirken bir sunucu hatası oluştu.",
        ) from err


@router.patch("/books/{file_hash}")
async def update_book(
    file_hash: str,
    request: Request,
    payload: BookUpdateRequest,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Update book endpoint."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    await db.update_book(file_hash, payload.model_dump(exclude_unset=True))
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_STATS)
    notify_ws(WS_EVENT_LIBRARY_UPDATE, {})
    return {"status": "updated"}


@router.patch("/books/{file_hash}/favorite")
async def toggle_favorite(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Toggle favorite endpoint."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    new_status = await db.toggle_favorite(file_hash)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_STATS)
    notify_ws(WS_EVENT_LIBRARY_UPDATE, {})
    return {"status": "updated", "is_favorite": new_status}


@router.get(
    "/download/{file_hash}",
    responses={404: {"description": "Kitap veya dosya bulunamadı"}},
)
async def download_book(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> Response:
    """Download/stream book endpoint with ETag 304 and HTTP Range support."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    row = await db.get_book_path(file_hash)
    if not row:
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)

    path, name = row
    safe_path = os.path.realpath(os.path.abspath(path))
    if not is_path_within(LIBRARY_ROOT, safe_path):
        log_event(
            "security",
            "ERROR",
            "Download blocked for file outside library",
            file_hash=file_hash,
        )
        raise HTTPException(status_code=404, detail="File not found on disk")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    stat_res = os.stat(safe_path)
    etag = f'"{file_hash[:16]}-{stat_res.st_mtime_ns:x}-{stat_res.st_size:x}"'
    inm = request.headers.get("if-none-match", "")
    if inm and etag in inm and not request.headers.get("range"):
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=3600",
                "Accept-Ranges": "bytes",
            },
        )

    media_type = "application/pdf"
    lower_path = safe_path.lower()
    if lower_path.endswith(EXT_EPUB):
        media_type = "application/epub+zip"
    elif lower_path.endswith(EXT_TXT):
        media_type = "text/plain; charset=utf-8"

    return FileResponse(
        safe_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename*=utf-8''{quote(name)}",
            "Accept-Ranges": "bytes",
            "ETag": etag,
            "Cache-Control": "private, max-age=3600",
        },
    )


@router.get(
    "/books/{file_hash}/reader-content",
    responses={
        400: {"description": "Yalnızca EPUB ve TXT belgeleri için yapılandırılmış metin döner"},
        404: {"description": "Kitap veya dosya bulunamadı"},
    },
)
async def get_reader_content(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Return structured paginated pages and TOC for in-browser EPUB and TXT reading."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    row = await db.get_book_path(file_hash)
    if not row:
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)

    path, name = row
    safe_path = os.path.realpath(os.path.abspath(path))
    if not is_path_within(LIBRARY_ROOT, safe_path) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    lower_path = safe_path.lower()
    if not lower_path.endswith((EXT_EPUB, EXT_TXT)):
        raise HTTPException(status_code=400, detail="Structured reader content applies to EPUB/TXT")

    from app.epub import extract_structured_reader_pages

    data = await asyncio.to_thread(extract_structured_reader_pages, safe_path)
    total_pages = int(data.get("total_pages") or 0)
    if total_pages > 0 and await db._has_page_size_columns():
        await db.conn.execute(
            "UPDATE kitaplar SET sayfa_sayisi = ? WHERE dosya_hash = ? AND COALESCE(sayfa_sayisi, 0) = 0",
            (total_pages, file_hash),
        )
        await db.conn.commit()

    return {
        "file_hash": file_hash,
        "filename": name,
        **data,
    }


@router.patch(
    "/books/{file_hash}/progress",
    responses={400: {"description": "Geçersiz sayfa numarası"}},
)
async def save_progress(
    file_hash: str,
    request: Request,
    payload: SaveProgressRequest,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Save reading progress (and sync total page count if provided)."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    if payload.page < 1 or payload.page > 100000:
        raise HTTPException(status_code=400, detail="Invalid page number")
    await db.update_reading_progress(file_hash, payload.page, total_pages=payload.total_pages)
    return {"status": "updated", "page": payload.page, "total_pages": payload.total_pages}


@router.get("/books/{file_hash}/annotations")
async def get_annotations(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Get all highlights and notes for a book."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    annotations = await db.get_book_annotations(file_hash)
    return {"status": STATUS_SUCCESS, "annotations": annotations}


@router.post("/books/{file_hash}/annotations")
async def save_annotation(
    file_hash: str,
    payload: AnnotationCreateRequest,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Save or update an individual highlight/note."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    ann_dict = payload.model_dump()
    ann_dict["dosya_hash"] = file_hash
    saved = await db.save_book_annotation(ann_dict)
    return {"status": "saved", "annotation": saved}


@router.delete(
    "/books/{file_hash}/annotations/{annotation_id}",
    responses={
        400: {"description": "Geçersiz not ID formatı"},
        404: {"description": "Not bulunamadı"},
    },
)
async def delete_annotation(
    file_hash: str,
    annotation_id: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Delete an individual highlight/note."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    if (
        not annotation_id
        or len(annotation_id) > 128
        or not re.match(r"^[a-zA-Z0-9_\-]+$", annotation_id)
    ):
        raise HTTPException(status_code=400, detail="Geçersiz not ID formatı")
    deleted = await db.delete_book_annotation(annotation_id, file_hash)
    if not deleted:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    return {"status": "deleted", "id": annotation_id}


@router.post("/books/{file_hash}/annotations/batch")
async def save_annotations_batch(
    file_hash: str,
    payload: AnnotationBatchRequest,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Batch save highlights/notes for synchronization."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    ann_list = []
    for ann in payload.annotations:
        ann_dict = ann.model_dump()
        ann_dict["dosya_hash"] = file_hash
        ann_list.append(ann_dict)
    saved_count = await db.save_book_annotations_batch(ann_list)
    return {"status": "success", "count": saved_count}


@router.get("/stats")
async def get_stats(request: Request, db: DatabaseManager = Depends(get_db)) -> dict:
    """Get library statistics."""
    _ensure_authorized(request)
    return await db.get_stats()


@router.get("/books/duplicates")
async def get_duplicate_books(request: Request, db: DatabaseManager = Depends(get_db)) -> dict:
    """Find and return groups of duplicate books."""
    _ensure_authorized(request)
    groups = await db.find_duplicate_books()
    return {
        "status": "success",
        "duplicates": groups,
        "duplicate_groups": groups,
        "total_groups": len(groups),
    }


@router.post(
    "/books/{file_hash}/compress",
    responses={
        400: {"description": "Yalnızca PDF belgeleri optimize edilebilir"},
        404: {"description": "Kitap dosyası veya fiziksel dosya bulunamadı"},
    },
)
async def compress_book_pdf(
    file_hash: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Locally compress a PDF file in-place to reclaim disk space."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)

    res = await db.get_book_path(file_hash)
    if not res or not res[0]:
        raise HTTPException(status_code=404, detail="Kitap dosyası veritabanında bulunamadı.")
    file_path, filename = res

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"Fiziksel kitap dosyası diskte bulunamadı: {file_path}",
        )

    if not filename.lower().endswith(EXT_PDF):
        raise HTTPException(status_code=400, detail="Yalnızca PDF belgeleri optimize edilebilir.")

    from app.services.pdf_compressor import pdf_compressor

    result = await pdf_compressor.compress_pdf(file_path)

    if result.get("success") and result.get("optimized"):
        await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
        await FastAPICache.clear(namespace=CACHE_NAMESPACE_STATS)
        notify_ws(
            WS_EVENT_LIBRARY_UPDATE,
            {"reason": "compress_complete", "file_hash": file_hash},
        )

    return result


@router.post(
    "/books/{file_hash}/cover",
    responses={
        400: {"description": "Yalnızca resim dosyalarına izin verilir veya geçersiz resim"},
        404: {"description": "Kitap bulunamadı"},
        413: {"description": "Kapak resmi boyutu çok büyük"},
        500: {"description": "Kapak resmi kaydedilemedi veya işleme hatası"},
    },
)
async def upload_cover(
    file_hash: str,
    request: Request,
    file: UploadFile = File(...),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Upload cover image."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    if not await db.book_exists(file_hash):
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)

    content = await read_limited_upload(file, MAX_COVER_BYTES, "Cover image")
    thumb_dir = THUMBNAILS_DIR
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_path = os.path.join(thumb_dir, f"{file_hash}.jpg")

    def _process_and_save_cover() -> None:
        os.makedirs(thumb_dir, exist_ok=True)
        img = prepare_cover_image(content, MAX_IMAGE_PIXELS)
        try:
            img.thumbnail((400, 560), Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=90)
        finally:
            img.close()

    try:
        await asyncio.to_thread(_process_and_save_cover)
        await db.conn.execute(
            "UPDATE kitaplar SET has_cover = 1 WHERE dosya_hash = ?", (file_hash,)
        )
        await db.conn.commit()
        await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
        notify_ws(WS_EVENT_LIBRARY_UPDATE, {"reason": "cover_updated", "file_hash": file_hash})
        log_event(LOG_CAT_FILESYSTEM, "INFO", "Cover image updated", file_hash=file_hash)
        return {"status": "updated", "thumbnail": f"/thumbnails/{file_hash}.jpg?v={int(time.time())}"}
    except ValueError as val_err:
        log_event(
            LOG_CAT_FILESYSTEM,
            "WARNING",
            f"Kapak resmi doğrulaması başarısız oldu: {val_err}",
            file_hash=file_hash,
        )
        raise HTTPException(status_code=400, detail=str(val_err)) from val_err
    except OSError as os_err:
        log_event(
            LOG_CAT_FILESYSTEM,
            "ERROR",
            f"Kapak resmi kaydedilirken disk/OS hatası oluştu: {os_err}",
            file_hash=file_hash,
        )
        raise HTTPException(status_code=500, detail="Kapak resmi kaydedilemedi.") from None
    except Exception as e:
        log_event(
            LOG_CAT_FILESYSTEM,
            "ERROR",
            f"Kapak yüklenirken beklenmedik hata oluştu: {e}",
            file_hash=file_hash,
        )
        raise HTTPException(status_code=500, detail="Image processing failed") from None


@router.get("/books/{file_hash}/toc")
async def get_book_toc(
    file_hash: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Get or auto-generate TOC (outline) with page offset solving."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    from app.services.toc_service import toc_service

    items = await toc_service.get_or_generate_toc(db, file_hash)
    return {"file_hash": file_hash, "items": items, "count": len(items)}


@router.get(
    "/books/{file_hash}/export/{export_format}",
    responses={
        400: {"description": "Desteklenmeyen dışa aktarım formatı"},
        404: {"description": "Kitap bulunamadı"},
    },
)
async def export_book_data(
    file_hash: str,
    export_format: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Export book notes and metadata to PKM platforms (Obsidian, Anki, BibTeX)."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)

    book = await db.get_book_by_hash(file_hash)
    if not book:
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)

    fmt = export_format.lower().strip()
    from app.services.pkm_exporter import PKMExporter
    from app.utils import sanitize_export_stem

    raw_title = book.get("kitap_adi") or "kitap"
    clean_title = sanitize_export_stem(raw_title, default="kitap")

    if fmt in ("obsidian", "markdown", "md"):
        annotations = await db.get_book_annotations(file_hash)
        content = PKMExporter.export_obsidian(book, annotations)
        filename = f"{clean_title}.md"
        media_type = "text/markdown; charset=utf-8"

    elif fmt in ("anki", "tsv"):
        annotations = await db.get_book_annotations(file_hash)
        content = PKMExporter.export_anki(book, annotations)
        filename = f"{clean_title}_anki.tsv"
        media_type = "text/tab-separated-values; charset=utf-8"

    elif fmt in ("bibtex", "bib"):
        content = PKMExporter.export_bibtex(book)
        filename = f"{clean_title}.bib"
        media_type = "application/x-bibtex; charset=utf-8"

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format '{export_format}'. Supported: obsidian, anki, bibtex",
        )

    safe_name = quote(filename)
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
            "Cache-Control": "no-cache",
        },
    )


@router.get("/books/embedding-status")
async def get_embedding_status(
    request: Request, db: DatabaseManager = Depends(get_db)
) -> dict[str, Any]:
    """Return breakdown of active semantic embedding models across indexed book chunks."""
    _ensure_authorized(request)
    from app.services.embedding_service import embedding_service

    models_breakdown: dict[str, int] = {}
    try:
        cur = await db.conn.execute(
            "SELECT COALESCE(embedding_model, 'hash-v1') AS m, COUNT(*) FROM kitap_chunks GROUP BY m"
        )
        for m_name, cnt in await cur.fetchall():
            models_breakdown[str(m_name)] = int(cnt)
    except Exception as err:
        log_event("database", "DEBUG", f"Embedding status query note: {err}")

    return {
        "status": STATUS_SUCCESS,
        "local_engine": embedding_service.active_local_model_id(),
        "models": models_breakdown,
        "total_chunks": sum(models_breakdown.values()),
    }


@router.post("/books/reindex-embeddings")
async def reindex_all_book_embeddings(
    request: Request,
    x_ai_provider: str | None = Header(None, alias="X-AI-Provider"),
    x_ai_key: str | None = Header(None, alias="X-AI-Key"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-Url"),
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Re-generate semantic vector embeddings for all books in the library in the background."""
    _ensure_authorized(request)
    cfg = load_config()
    provider, api_key, _, base_url = resolve_ai_credentials(
        provider=x_ai_provider,
        api_key=x_ai_key,
        model=None,
        base_url=x_ai_base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    cur = await db.conn.execute("SELECT dosya_hash, kitap_adi, dosya_yolu FROM kitaplar")
    books = [dict(r) for r in await cur.fetchall()]
    if not books:
        return {"status": STATUS_SUCCESS, "message": "İndekslenecek kitap bulunamadı.", "queued": 0}

    task_id = f"reindex-{uuid.uuid4().hex[:10]}"
    from app.tasks import ACTIVE_TASKS, update_task_status

    ACTIVE_TASKS[task_id] = {
        "filename": "Anlamsal Vektör Yeniden İndeksleme",
        "status": "processing",
        "percentage": 5,
        "log_message": f"{len(books)} kitap için anlamsal vektörler hazırlanıyor...",
        "last_update": time.time(),
        "logs": [],
    }

    async def _run_reindex_job() -> None:
        from app.database import get_db_context
        from app.services.chunking_service import DocumentChunker, index_document_chunks
        from app.services.embedding_service import embedding_service
        from app.utils import resolve_portable_book_path

        reindexed_books = 0
        total_books = max(1, len(books))
        used_model = embedding_service.active_local_model_id()
        try:
            async with get_db_context() as bg_db:
                for idx_b, b_row in enumerate(books):
                    b_hash = str(b_row.get("dosya_hash") or "")
                    b_title = str(b_row.get("kitap_adi") or "Kitap")
                    pct = min(96, max(8, int(((idx_b + 1) / total_books) * 92)))
                    update_task_status(
                        task_id,
                        "processing",
                        pct,
                        f"Anlamsal vektör üretiliyor ({idx_b + 1}/{total_books}): {b_title}",
                    )
                    cur_c = await bg_db.conn.execute(
                        "SELECT sayfa_no, chunk_index, metin, char_count FROM kitap_chunks WHERE dosya_hash = ? ORDER BY chunk_index ASC",
                        (b_hash,),
                    )
                    existing_rows = await cur_c.fetchall()
                    if existing_rows:
                        chunks = [
                            {
                                "dosya_hash": b_hash,
                                "sayfa_no": int(r[0]),
                                "chunk_index": int(r[1]),
                                "metin": str(r[2]),
                                "char_count": int(r[3]),
                            }
                            for r in existing_rows
                        ]
                    else:
                        raw_p = str(b_row.get("dosya_yolu") or "")
                        resolved_p = resolve_portable_book_path(raw_p, LIBRARY_ROOT) if raw_p else ""
                        if not resolved_p or not os.path.exists(resolved_p):
                            continue
                        chunks = await asyncio.to_thread(
                            DocumentChunker.chunk_document, resolved_p, b_hash
                        )
                    if not chunks:
                        continue
                    texts = [c["metin"] for c in chunks]
                    blobs, used_model = await asyncio.to_thread(
                        embedding_service.generate_semantic_embeddings_batch,
                        texts,
                        provider,
                        api_key,
                        base_url,
                    )
                    await index_document_chunks(
                        bg_db, chunks, embeddings=blobs, embedding_model=used_model
                    )
                    reindexed_books += 1

            update_task_status(
                task_id,
                STATUS_SUCCESS,
                100,
                f"{reindexed_books} kitabın anlamsal vektörleri güncellendi ({used_model}).",
            )
            log_event(
                "database",
                "INFO",
                f"Anlamsal vektör yeniden indeksleme tamamlandı ({reindexed_books} kitap, motor: {used_model}).",
            )
        except Exception as job_err:
            update_task_status(task_id, "error", 100, f"Vektör indeksleme hatası: {job_err}")
            log_event("database", "ERROR", f"Reindex embeddings hatası: {job_err}")

    bg_task = asyncio.create_task(_run_reindex_job())
    bg_set = getattr(request.app.state, "background_tasks", None)
    if isinstance(bg_set, set):
        bg_set.add(bg_task)
        bg_task.add_done_callback(bg_set.discard)

    return {
        "status": STATUS_SUCCESS,
        "task_id": task_id,
        "queued": len(books),
        "message": f"{len(books)} kitap için arka planda anlamsal vektör indeksleme başlatıldı.",
    }


@router.get("/books/{file_hash}/ocr-page/{page_num}")
async def get_scanned_page_ocr_layer(
    file_hash: str,
    page_num: int,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Extract or load cached normalized word-box OCR coordinates for a scanned PDF page."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    if page_num < 1 or page_num > 10000:
        raise HTTPException(status_code=400, detail="Geçersiz sayfa numarası.")

    row = await db.get_book_path(file_hash)
    if not row:
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)
    path, _ = row
    safe_path = os.path.realpath(os.path.abspath(path))
    if not is_path_within(LIBRARY_ROOT, safe_path) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Dosya diskte bulunamadı.")
    if not safe_path.lower().endswith(EXT_PDF):
        raise HTTPException(status_code=400, detail="OCR katmanı yalnızca PDF belgeleri içindir.")

    from app.services.ocr_layer_service import ocr_layer_service

    return await ocr_layer_service.get_or_extract_page_ocr(db, file_hash, safe_path, page_num)


@router.post("/books/{file_hash}/ocr-index")
async def trigger_full_book_ocr_index(
    file_hash: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Start a background job to OCR all scanned pages of a PDF and index them into FTS5 + vectors."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    row = await db.get_book_path(file_hash)
    if not row:
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)
    path, filename = row
    safe_path = os.path.realpath(os.path.abspath(path))
    if not is_path_within(LIBRARY_ROOT, safe_path) or not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Dosya diskte bulunamadı.")
    if not safe_path.lower().endswith(EXT_PDF):
        raise HTTPException(status_code=400, detail="OCR indeksleme yalnızca PDF içindir.")

    from app.pdf import get_pdf_page_count
    from app.tasks import ACTIVE_TASKS, update_task_status

    total_pages = await asyncio.to_thread(get_pdf_page_count, safe_path)
    task_id = f"ocr-{uuid.uuid4().hex[:10]}"
    ACTIVE_TASKS[task_id] = {
        "filename": f"OCR Katmanı: {filename}",
        "status": "processing",
        "percentage": 5,
        "log_message": f"{total_pages} sayfalık taranmış belge OCR kuyruğuna alındı...",
        "last_update": time.time(),
        "logs": [],
    }

    async def _run_full_ocr_job() -> None:
        from app.database import get_db_context
        from app.services.chunking_service import _split_text_into_chunks, index_document_chunks
        from app.services.embedding_service import embedding_service
        from app.services.ocr_layer_service import ocr_layer_service

        try:
            all_chunks: list[dict[str, Any]] = []
            chunk_idx = 0
            max_p = max(1, min(total_pages, 400))
            async with get_db_context() as bg_db:
                for p_no in range(1, max_p + 1):
                    pct = min(94, max(6, int((p_no / max_p) * 90)))
                    update_task_status(
                        task_id,
                        "processing",
                        pct,
                        f"Sayfa {p_no}/{max_p} OCR metin katmanı çıkarılıyor...",
                    )
                    res_p = await ocr_layer_service.get_or_extract_page_ocr(
                        bg_db, file_hash, safe_path, p_no
                    )
                    ft = str(res_p.get("full_text") or "").strip()
                    if ft:
                        for c_txt in _split_text_into_chunks(ft, max_chars=600):
                            all_chunks.append(
                                {
                                    "dosya_hash": file_hash,
                                    "sayfa_no": p_no,
                                    "chunk_index": chunk_idx,
                                    "metin": c_txt,
                                    "char_count": len(c_txt),
                                }
                            )
                            chunk_idx += 1

                if all_chunks:
                    texts = [c["metin"] for c in all_chunks]
                    blobs, model_id = await asyncio.to_thread(
                        embedding_service.generate_semantic_embeddings_batch, texts
                    )
                    await index_document_chunks(
                        bg_db, all_chunks, embeddings=blobs, embedding_model=model_id
                    )

            update_task_status(
                task_id,
                STATUS_SUCCESS,
                100,
                f"Taranmış PDF OCR tamamlandı ({len(all_chunks)} aranabilir pasaj).",
            )
        except Exception as ocr_job_err:
            update_task_status(task_id, "error", 100, f"OCR indeksleme hatası: {ocr_job_err}")
            log_event("pdf", "ERROR", f"Full OCR index hatası ({filename}): {ocr_job_err}")

    bg_task = asyncio.create_task(_run_full_ocr_job())
    bg_set = getattr(request.app.state, "background_tasks", None)
    if isinstance(bg_set, set):
        bg_set.add(bg_task)
        bg_task.add_done_callback(bg_set.discard)

    return {"status": STATUS_SUCCESS, "task_id": task_id, "total_pages": total_pages}


@router.get("/books/{file_hash}/bookmarks")
async def get_book_bookmarks_endpoint(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict[str, Any]:
    """Return all saved page bookmarks for a book."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    items = await db.get_book_bookmarks(file_hash)
    return {"status": STATUS_SUCCESS, "bookmarks": items}


@router.post("/books/{file_hash}/bookmarks")
async def toggle_book_bookmark_endpoint(
    file_hash: str,
    payload: BookmarkToggleRequest,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Toggle or save a page bookmark for a book."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    res = await db.toggle_or_save_bookmark(
        file_hash, payload.sayfa_no, etiket=payload.etiket, toggle=payload.toggle
    )
    return {"status": STATUS_SUCCESS, **res}


@router.delete("/books/{file_hash}/bookmarks/{page_num}")
async def delete_book_bookmark_endpoint(
    file_hash: str,
    page_num: int,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Delete a page bookmark by page number."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    deleted = await db.delete_book_bookmark(file_hash, page_num)
    return {"status": STATUS_SUCCESS, "deleted": deleted, "sayfa_no": page_num}


@router.get("/books/{file_hash}/epub-asset")
async def serve_epub_embedded_asset(
    file_hash: str,
    path: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Securely stream an embedded image resource from inside an EPUB archive."""
    import zipfile

    from app.epub import safe_read_zip_entry

    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)

    clean_rel = path.strip().lstrip("/").replace("\\", "/")
    norm_rel = os.path.normpath(clean_rel).replace("\\", "/")
    if not norm_rel or norm_rel.startswith("..") or "/../" in f"/{norm_rel}/":
        raise HTTPException(status_code=400, detail="Geçersiz EPUB varlık yolu.")

    allowed_media = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }
    _, ext = os.path.splitext(norm_rel.lower())
    if ext not in allowed_media:
        raise HTTPException(status_code=400, detail="Yalnızca gömülü görsel varlıkları desteklenir.")

    row = await db.get_book_path(file_hash)
    if not row:
        raise HTTPException(status_code=404, detail=ERR_BOOK_NOT_FOUND)
    book_path, _ = row
    safe_book_path = os.path.realpath(os.path.abspath(book_path))
    if (
        not is_path_within(LIBRARY_ROOT, safe_book_path)
        or not os.path.exists(safe_book_path)
        or not safe_book_path.lower().endswith(EXT_EPUB)
    ):
        raise HTTPException(status_code=404, detail="EPUB dosyası bulunamadı.")

    def _read_asset_bytes() -> bytes | None:
        with zipfile.ZipFile(safe_book_path, "r") as zf:
            if norm_rel in zf.namelist():
                return safe_read_zip_entry(zf, norm_rel, max_bytes=12 * 1024 * 1024)
            if clean_rel in zf.namelist():
                return safe_read_zip_entry(zf, clean_rel, max_bytes=12 * 1024 * 1024)
        return None

    asset_bytes = await asyncio.to_thread(_read_asset_bytes)
    if not asset_bytes:
        raise HTTPException(status_code=404, detail="Gömülü EPUB görseli bulunamadı.")

    return Response(
        content=asset_bytes,
        media_type=allowed_media[ext],
        headers={
            "Cache-Control": "private, max-age=86400",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; img-src data:;",
            "X-Content-Type-Options": "nosniff",
        },
    )
