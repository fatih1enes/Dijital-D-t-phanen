import asyncio
import json
import os
import re
import time
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi_cache import FastAPICache

from app.auth import _ensure_authorized
from app.database import DatabaseManager
from app.dependencies import get_db
from app.logger import log_event
from app.models import CollectionAddBookRequest, CollectionCreateRequest
from app.utils import sanitize_filename, validate_file_hash

router = APIRouter(prefix="/api", tags=["collections"])

CACHE_NAMESPACE_COLLECTIONS = "collections"
CACHE_NAMESPACE_BOOKS = "books"
KEY_BOOK_HASHES = "book_hashes"


@router.get("/collections")
async def get_collections(request: Request, db: DatabaseManager = Depends(get_db)) -> list[dict]:
    """Get all collections."""
    _ensure_authorized(request)
    return await db.get_collections()


@router.post(
    "/collections",
    responses={400: {"description": "Name required, too long, or collection already exists"}},
)
async def create_collection(
    request: Request,
    payload: CollectionCreateRequest | None = None,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Create collection."""
    _ensure_authorized(request)

    is_dynamic = False
    rule_json = None
    if payload is not None:
        name = payload.isim
        is_dynamic = payload.is_dynamic
        rule_json = payload.rule_json
    else:
        data = await request.json()
        raw = data if isinstance(data, dict) else {}
        name = re.sub(r"\s+", " ", str(raw.get("isim") or "")).strip()
        is_dynamic = bool(raw.get("is_dynamic"))
        rule_json = raw.get("rule_json")
        if isinstance(rule_json, dict):
            rule_json = json.dumps(rule_json, ensure_ascii=False)

    if not name:
        raise HTTPException(status_code=400, detail="Name required")
    if len(name) > 120:
        raise HTTPException(status_code=400, detail="Name too long")

    result = await db.add_collection(name, is_dynamic=is_dynamic, rule_json=rule_json)
    if not result:
        raise HTTPException(status_code=400, detail="Collection already exists")

    await FastAPICache.clear(namespace=CACHE_NAMESPACE_COLLECTIONS)
    return result


@router.post("/collections/{col_id}/books")
async def add_book_to_collection(
    col_id: int,
    request: Request,
    payload: CollectionAddBookRequest | None = None,
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Add book to collection."""
    _ensure_authorized(request)

    if payload is not None:
        book_hash = validate_file_hash(payload.kitap_hash)
    else:
        data = await request.json()
        raw = data if isinstance(data, dict) else {}
        book_hash = validate_file_hash(str(raw.get("kitap_hash") or ""))

    await db.add_book_to_col(col_id, book_hash)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_COLLECTIONS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    return {"status": "added"}


@router.delete("/collections/{col_id}/books/{file_hash}")
async def remove_book_from_collection(
    col_id: int, file_hash: str, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Remove book from collection."""
    file_hash = validate_file_hash(file_hash)
    _ensure_authorized(request)

    await db.rm_book_from_col(col_id, file_hash)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_COLLECTIONS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    return {"status": "removed"}


@router.delete("/collections/{col_id}")
async def delete_collection(
    col_id: int, request: Request, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Delete collection."""
    _ensure_authorized(request)

    await db.delete_collection(col_id)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_COLLECTIONS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    return {"status": "deleted"}


@router.get("/share-collection/{col_id}")
async def export_collection(
    col_id: int, request: Request, db: DatabaseManager = Depends(get_db)
) -> Response:
    """Export collection as JSON."""
    _ensure_authorized(request)

    log_event("system", "INFO", f"Koleksiyon dışa aktarılıyor (ID: {col_id})")
    books = await db.get_collection_books(col_id)
    log_event("system", "INFO", f"Koleksiyon (ID: {col_id}) için {len(books)} kitap bulundu.")
    col_name = await db.get_collection_name(col_id)

    export_data = {
        "koleksiyon_adi": col_name,
        "dis_aktarim_tarihi": time.strftime("%Y-%m-%d %H:%M:%S"),
        "kitaplar": books,
    }

    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    filename = f"{sanitize_filename(col_name)}_export.json"

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{quote(filename)}"},
    )


@router.post(
    "/collections/import",
    responses={
        400: {"description": "Koleksiyon boş veya geçersiz format"},
        413: {"description": "Dosya boyutu çok büyük"},
        500: {"description": "Koleksiyon oluşturulamadı"},
    },
)
async def import_collection(
    request: Request,
    file: UploadFile = File(...),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """Import collection from JSON."""
    _ensure_authorized(request)

    from app.constants import MAX_UPLOAD_BYTES
    from app.routers.books import read_limited_upload

    content = await read_limited_upload(file, MAX_UPLOAD_BYTES, "Koleksiyon dosyası")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as decode_err:
        log_event(
            "system",
            "WARNING",
            f"Koleksiyon içe aktarımında geçersiz JSON yapısı: {decode_err}",
        )
        raise HTTPException(
            status_code=400, detail=f"Geçersiz JSON dosyası: {decode_err.msg}"
        ) from None

    col_name = data.get("koleksiyon_adi", "İçe Aktarılan Koleksiyon")
    books = data.get("kitaplar", [])
    if not books:
        raise HTTPException(status_code=400, detail="Koleksiyon boş veya geçersiz format")

    new_col = await db.add_collection(f"{col_name} (İçe Aktarıldı)")
    if not new_col:
        new_col = await db.add_collection(f"{col_name} ({int(time.time())})")
    if not new_col:
        raise HTTPException(status_code=500, detail="Koleksiyon oluşturulamadı")

    col_id = new_col["id"]
    added_count = 0
    for b in books:
        h = b.get("dosya_hash")
        if h and await db.book_exists(h):
            await db.add_book_to_col(col_id, h)
            added_count += 1

    await FastAPICache.clear(namespace=CACHE_NAMESPACE_COLLECTIONS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    return {"status": "success", "collection": new_col, "added_books": added_count}


def _parse_cluster_json(response_text: str) -> list[dict]:
    """Extract and parse JSON array of clusters from AI response text."""
    clean_text = response_text.strip()
    if "```" in clean_text:
        fence_match = re.search(r"```(?:json)?\s*(\[[^\]]*\])\s*```", clean_text, re.DOTALL)
        if fence_match:
            clean_text = fence_match.group(1)
    start_idx = clean_text.find("[")
    end_idx = clean_text.rfind("]")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            parsed = json.loads(clean_text[start_idx : end_idx + 1])
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return []
    return []


def _fallback_category_clusters(catalog: list[dict]) -> list[dict]:
    """Group catalog into clusters based on book category."""
    cat_groups: dict[str, list[str]] = {}
    for b in catalog:
        cat_name = b["category"] or "Genel Okuma"
        cat_groups.setdefault(cat_name, []).append(b["hash"])

    return [
        {
            "name": cat_name,
            "description": f"{cat_name} alanındaki kitaplar",
            KEY_BOOK_HASHES: hashes,
        }
        for cat_name, hashes in cat_groups.items()
    ]


async def _apply_clusters_to_db(clusters: list[dict], db: DatabaseManager) -> list[dict]:
    """Persist generated clusters as collections in database."""
    created = []
    for c in clusters:
        name = c.get("name")
        hashes = c.get(KEY_BOOK_HASHES, [])
        if not name or not hashes:
            continue
        new_col = await db.add_collection(name)
        if not new_col:
            new_col = await db.add_collection(f"{name} ({int(time.time())})")
        if new_col:
            col_id = new_col["id"]
            for h in hashes:
                if await db.book_exists(h):
                    await db.add_book_to_col(col_id, h)
            created.append(new_col)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_COLLECTIONS)
    await FastAPICache.clear(namespace=CACHE_NAMESPACE_BOOKS)
    return created


@router.post("/collections/auto-cluster")
async def auto_cluster_collections(
    request: Request, apply: bool = False, db: DatabaseManager = Depends(get_db)
) -> dict:
    """Analyze books and cluster them into thematic smart collections using AI or category heuristics."""
    _ensure_authorized(request)

    books_data = await db.get_all_books(limit=500)
    all_books = books_data.get("items", []) if isinstance(books_data, dict) else (books_data or [])
    if not all_books:
        return {
            "status": "empty",
            "clusters": [],
            "message": "Kütüphanede henüz kitap bulunmuyor.",
        }

    # Prepare catalog data
    catalog = []
    book_map = {}
    for b in all_books:
        h = b.get("dosya_hash")
        if not h:
            continue
        title = b.get("kitap_adi") or b.get("dosya_adi") or "İsimsiz"
        author = b.get("yazar") or ""
        cat = b.get("kategori") or ""
        subcat = b.get("alt_kategori") or ""
        summary = (b.get("ozet") or "")[:180]
        catalog.append(
            {
                "hash": h,
                "title": title,
                "author": author,
                "category": cat,
                "subcat": subcat,
                "summary": summary,
            }
        )
        book_map[h] = title

    from app.config import load_config

    config = load_config()
    provider = config.get("ai_provider", "gemini")
    api_key = config.get("ai_api_key") or os.environ.get("GEMINI_API_KEY", "")
    model = config.get("gemini_model", None)

    clusters = []
    if api_key and len(catalog) >= 2:
        if len(catalog) > 50:
            log_event(
                "system",
                "INFO",
                f"Koleksiyon kümeleme: Toplam {len(catalog)} kitaptan ilk 50'si AI analizine dahil ediliyor.",
            )
        catalog_sample = catalog[:50]
        prompt = (
            "Aşağıdaki kitap listesini konularına, türlerine veya temalarına göre 2 ila 6 adet anlamlı, çekici ve mantıklı KOLEKSİYON (küme) altında topla.\n"
            f"{json.dumps(catalog_sample, ensure_ascii=False)}\n\n"
            "GÖREV:\n"
            "Her koleksiyon için bir başlık (name), 1 cümlelik açıklama (description) ve eşleşen kitapların 'hash' kodlarını ver.\n"
            "ÇIKTI FORMATI: Yanıtını SADECE ve KESİNLİKLE aşağıdaki JSON formatında döndür, markdown veya ek metin yazma:\n"
            "[\n"
            "  {\n"
            '    "name": "Koleksiyon Adı",\n'
            '    "description": "Açıklama",\n'
            '    "book_hashes": ["hash1", "hash2"]\n'
            "  }\n"
            "]"
        )
        try:
            from app.ai_router import generate_ai_response

            response_text = await asyncio.to_thread(
                generate_ai_response,
                prompt=prompt,
                provider=provider,
                api_key=api_key,
                model=model,
                system_instruction="Sen deneyimli bir kütüphanecisin. Kitapları tematik koleksiyonlara grupla ve yalnızca JSON listesi dön.",
            )
            clusters = _parse_cluster_json(response_text)
        except Exception as e:
            log_event("system", "WARNING", f"Akıllı koleksiyon AI kümeleme hatası: {e}")

    # Fallback to category-based clustering
    if not clusters:
        clusters = _fallback_category_clusters(catalog)

    # Enrich with book titles
    for c in clusters:
        c["book_titles"] = [book_map.get(h, "Kitap") for h in c.get(KEY_BOOK_HASHES, [])]

    # Automatically create collections in database if apply=True
    created_collections = []
    if apply:
        created_collections = await _apply_clusters_to_db(clusters, db)

    return {
        "status": "success",
        "clusters": clusters,
        "applied": apply,
        "created_count": len(created_collections),
    }
