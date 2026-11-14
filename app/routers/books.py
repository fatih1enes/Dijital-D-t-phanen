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
    BookOrderRequest,
    BookUpdateRequest,
    SaveProgressRequest,
)
from app.pdf import prepare_cover_image
from app.tasks import active_tasks
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
    offset = (page - 1) * limit
    return await db.get_all_books(
        limit=limit,
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
    results = await hybrid_search_engine.deep_search_pages(db, query=clean_q, limit=limit)
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
    active_tasks[task_id] = task_entry

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

    def _scan_library_files() -> list[str]:
        scanned = []
        for ext in ("*.pdf", "*.epub", "*.txt"):
            pattern = os.path.join(LIBRARY_ROOT, "**", ext)
            scanned.extend(glob.glob(pattern, recursive=True))
        return scanned

    scanned_files = await asyncio.to_thread(_scan_library_files)

    def _copy_to_temp(src_path: str, suffix: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
            shutil.copy2(src_path, tmp.name)
            return tmp.name

    enqueued_count = 0
    for file_path in scanned_files:
        if _is_ignorable_sync_file(file_path):
            continue

        try:
            file_hash = await asyncio.to_thread(get_file_hash_from_path, file_path)
            if await db.book_exists(file_hash):
                continue

            _, f_ext = os.path.splitext(file_path)
            tmp_path = await asyncio.to_thread(_copy_to_temp, file_path, f_ext.lower())

            filename = os.path.basename(file_path)
            task_id = str(uuid.uuid4())
            active_tasks[task_id] = {
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
            }

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
            enqueued_count += 1
        except Exception as e:
            log_event(
                "system",
                "ERROR",
                f"Taranan belge dosyası '{file_path}' işlenirken hata: {e}",
            )

    return {"status": "success", "enqueued_count": enqueued_count}


@router.delete("/books/{file_hash}")
async def delete_book(
    file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Delete book endpoint."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    await db.delete_book(file_hash)
    from app.services.session_manager import book_session_manager

    book_session_manager.clear_session(file_hash)
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
) -> FileResponse:
    """Download book endpoint."""
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

    media_type = "application/pdf"
    lower_path = safe_path.lower()
    if lower_path.endswith(EXT_EPUB):
        media_type = "application/epub+zip"
    elif lower_path.endswith(EXT_TXT):
        media_type = "text/plain; charset=utf-8"

    return FileResponse(
        safe_path,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=utf-8''{quote(name)}"},
    )


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
    """Save reading progress."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)
    if payload.page < 1 or payload.page > 100000:
        raise HTTPException(status_code=400, detail="Invalid page number")
    await db.update_reading_progress(file_hash, payload.page)
    return {"status": "updated", "page": payload.page}


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

    try:
        img = prepare_cover_image(content, MAX_IMAGE_PIXELS)
        img.thumbnail((400, 560), Image.Resampling.LANCZOS)
        img.save(thumb_path, "JPEG", quality=90)
        img.close()
        await db.conn.execute(
            "UPDATE kitaplar SET has_cover = 1 WHERE dosya_hash = ?", (file_hash,)
        )
        await db.conn.commit()
        await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
        log_event(LOG_CAT_FILESYSTEM, "INFO", "Cover image updated", file_hash=file_hash)
        return {"status": "updated", "thumbnail": f"/thumbnails/{file_hash}.jpg"}
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
    from app.utils import sanitize_filename

    raw_title = book.get("kitap_adi") or "kitap"
    clean_title = sanitize_filename(raw_title) or "kitap"

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
