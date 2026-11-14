"""OPDS 1.2 (Open Publication Distribution System) catalog router.

Provides standard Atom/OPDS feeds for e-reader integration (Moon+ Reader,
Apple Books, Kobo, KOReader, Aldiko, Thorium Reader, etc.).
"""

import base64
import html
import os
import secrets
from datetime import datetime, timezone
from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse

from app import auth as auth_mod
from app.constants import THUMBNAILS_DIR
from app.database import DatabaseManager
from app.dependencies import get_db
from app.logger import log_event
from app.utils import is_path_within, validate_file_hash

router = APIRouter(prefix="/opds", tags=["opds"])

OPDS_NAV_MIME = "application/atom+xml;profile=opds-catalog;kind=navigation; charset=utf-8"
OPDS_ACQ_MIME = "application/atom+xml;profile=opds-catalog;kind=acquisition; charset=utf-8"
OPENSEARCH_MIME = "application/opensearchdescription+xml; charset=utf-8"
MIME_JPEG = "image/jpeg"
MIME_EPUB = "application/epub+zip"
MIME_TXT = "text/plain; charset=utf-8"
MIME_PDF = "application/pdf"


def _check_opds_basic_auth(auth_header: str, active_password: str) -> bool:
    """Validate HTTP Basic Authentication header for OPDS."""
    if not auth_header.startswith("Basic "):
        return False
    try:
        b64_payload = auth_header[6:].strip()
        decoded = base64.b64decode(b64_payload).decode("utf-8")
        if ":" in decoded:
            _, provided_pwd = decoded.split(":", 1)
        else:
            provided_pwd = decoded
        return secrets.compare_digest(provided_pwd, active_password)
    except Exception as e:
        log_event("security", "DEBUG", f"OPDS Basic Auth decode error: {e}")
        return False


def _check_opds_token(token: str) -> bool:
    """Validate token against active auth tokens."""
    if not token or token not in auth_mod.AUTH_STATE.get("valid_tokens", {}):
        return False
    import time

    return time.time() <= auth_mod.AUTH_STATE["valid_tokens"][token]


def _ensure_opds_auth(request: Request) -> None:
    """Ensure OPDS request is authorized. Supports Localhost, Session Cookie, and HTTP Basic Auth."""
    if auth_mod._is_local_request(request):
        return

    active_password = auth_mod._get_access_password()
    if not active_password:
        if auth_mod._is_unprotected_remote_allowed():
            return
        raise HTTPException(
            status_code=401,
            detail="Remote access requires ACCESS_PASSWORD",
            headers={"WWW-Authenticate": 'Basic realm="Dijital Kutuphane OPDS"'},
        )

    # 1. Check existing session cookie
    if auth_mod._is_session_authenticated(request):
        return

    # 2. Check token in valid_tokens
    token = request.cookies.get(auth_mod.AUTH_COOKIE_NAME, "")
    if _check_opds_token(token):
        return

    # 3. Check HTTP Basic Authentication Header
    auth_header = request.headers.get("Authorization", "").strip()
    if _check_opds_basic_auth(auth_header, active_password):
        return

    # Not authorized: Send 401 with WWW-Authenticate header
    raise HTTPException(
        status_code=401,
        detail="OPDS Authentication Required",
        headers={"WWW-Authenticate": 'Basic realm="Dijital Kutuphane OPDS"'},
    )


def _format_iso(dt_val: str | None = None) -> str:
    """Format timestamp to ISO 8601 string for Atom feed."""
    if not dt_val:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        # If already ISO-like
        clean = dt_val.replace(" ", "T")
        if not clean.endswith("Z") and "+" not in clean:
            clean += "Z"
        return clean
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _xml_escape(text: str | None) -> str:
    """Safely escape text for XML content."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def _render_book_entry(book: dict, request: Request) -> str:
    """Render a single book as an OPDS acquisition <entry>."""
    title = _xml_escape(book.get("kitap_adi") or "İsimsiz Kitap")
    author = _xml_escape(book.get("yazar") or "Bilinmeyen Yazar")
    category = _xml_escape(book.get("kategori") or "Genel")
    summary = _xml_escape(book.get("ozet") or "Açıklama bulunmuyor.")
    file_hash = book.get("dosya_hash") or ""
    file_name = (book.get("dosya_adi") or "").lower()
    updated = _format_iso(book.get("ekleme_tarihi"))

    if file_name.endswith(".epub"):
        mime_type = MIME_EPUB
    elif file_name.endswith(".txt"):
        mime_type = MIME_TXT
    else:
        mime_type = MIME_PDF

    # Base URL for absolute or relative links
    base = str(request.base_url).rstrip("/")
    download_url = f"{base}/opds/download/{file_hash}"
    cover_url = f"{base}/opds/cover/{file_hash}"

    entry_xml = f"""  <entry>
    <title>{title}</title>
    <id>urn:dijital-kutuphane:book:{file_hash}</id>
    <author>
      <name>{author}</name>
    </author>
    <published>{updated}</published>
    <updated>{updated}</updated>
    <summary type="text">{summary}</summary>
    <category term="{category}" label="{category}" />
    <link rel="http://opds-spec.org/image" href="{cover_url}" type="{MIME_JPEG}" />
    <link rel="http://opds-spec.org/image/thumbnail" href="{cover_url}" type="{MIME_JPEG}" />
    <link rel="http://opds-spec.org/acquisition" href="{download_url}" type="{mime_type}" title="{title}" />
  </entry>"""
    return entry_xml


def _build_feed(
    feed_id: str,
    title: str,
    request: Request,
    self_href: str,
    entries_xml: str,
    subsections_xml: str = "",
    is_acquisition: bool = True,
) -> str:
    """Construct full Atom/OPDS XML document."""
    base = str(request.base_url).rstrip("/")
    now_iso = _format_iso()
    feed_mime = OPDS_ACQ_MIME if is_acquisition else OPDS_NAV_MIME

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>urn:dijital-kutuphane:opds:{feed_id}</id>
  <title>{_xml_escape(title)}</title>
  <updated>{now_iso}</updated>
  <author>
    <name>Dijital Kütüphane</name>
    <uri>{base}</uri>
  </author>
  <link rel="self" href="{_xml_escape(base + self_href)}" type="{feed_mime}" />
  <link rel="start" href="{base}/opds" type="{OPDS_NAV_MIME}" title="Ana Katalog" />
  <link rel="search" href="{base}/opds/opensearch.xml" type="{OPENSEARCH_MIME}" title="Kitap Ara" />
{subsections_xml}
{entries_xml}
</feed>"""
    return xml.strip()


@router.get("", response_class=Response)
@router.get("/catalog.xml", response_class=Response)
async def opds_root(request: Request) -> Response:
    """OPDS Root Navigation Feed."""
    _ensure_opds_auth(request)
    base = str(request.base_url).rstrip("/")

    # Subsections navigation links
    subsections = f"""  <link rel="subsection" href="{base}/opds/recent.xml" type="{OPDS_ACQ_MIME}" title="Son Eklenen Kitaplar" />
  <link rel="subsection" href="{base}/opds/all.xml" type="{OPDS_ACQ_MIME}" title="Tüm Kitaplar" />
  <link rel="subsection" href="{base}/opds/favorites.xml" type="{OPDS_ACQ_MIME}" title="Favori Kitaplarım" />
  <link rel="subsection" href="{base}/opds/categories.xml" type="{OPDS_NAV_MIME}" title="Kategoriler" />
  <link rel="subsection" href="{base}/opds/collections.xml" type="{OPDS_NAV_MIME}" title="Koleksiyonlar" />"""

    # Navigation entries for e-readers that prefer <entry> items in navigation feeds
    nav_entries = f"""  <entry>
    <title>Son Eklenen Kitaplar</title>
    <id>urn:dijital-kutuphane:opds:nav:recent</id>
    <updated>{_format_iso()}</updated>
    <content type="text">Kütüphaneye en son eklenen eserler</content>
    <link rel="subsection" href="{base}/opds/recent.xml" type="{OPDS_ACQ_MIME}" />
  </entry>
  <entry>
    <title>Tüm Kitaplar</title>
    <id>urn:dijital-kutuphane:opds:nav:all</id>
    <updated>{_format_iso()}</updated>
    <content type="text">Kütüphanedeki tüm kitapların tam listesi</content>
    <link rel="subsection" href="{base}/opds/all.xml" type="{OPDS_ACQ_MIME}" />
  </entry>
  <entry>
    <title>Favori Kitaplarım</title>
    <id>urn:dijital-kutuphane:opds:nav:favorites</id>
    <updated>{_format_iso()}</updated>
    <content type="text">Yıldızladığınız favori kitaplar</content>
    <link rel="subsection" href="{base}/opds/favorites.xml" type="{OPDS_ACQ_MIME}" />
  </entry>
  <entry>
    <title>Kategorilere Göre Gözat</title>
    <id>urn:dijital-kutuphane:opds:nav:categories</id>
    <updated>{_format_iso()}</updated>
    <content type="text">Tür ve kategoriye göre gruplanmış katalog</content>
    <link rel="subsection" href="{base}/opds/categories.xml" type="{OPDS_NAV_MIME}" />
  </entry>
  <entry>
    <title>Koleksiyonlar</title>
    <id>urn:dijital-kutuphane:opds:nav:collections</id>
    <updated>{_format_iso()}</updated>
    <content type="text">Oluşturduğunuz özel okuma listeleri ve koleksiyonlar</content>
    <link rel="subsection" href="{base}/opds/collections.xml" type="{OPDS_NAV_MIME}" />
  </entry>"""

    feed_xml = _build_feed(
        feed_id="root",
        title="Dijital Kütüphane Kataloğu",
        request=request,
        self_href="/opds",
        entries_xml=nav_entries,
        subsections_xml=subsections,
        is_acquisition=False,
    )
    return Response(content=feed_xml, media_type=OPDS_NAV_MIME)


@router.get("/recent.xml", response_class=Response)
async def opds_recent(request: Request, db: DatabaseManager = Depends(get_db)) -> Response:
    """Acquisition feed for recently added books."""
    _ensure_opds_auth(request)
    data = await db.get_all_books(limit=40, offset=0, sort="date_desc")
    books = data.get("items", [])

    entries = "\n".join(_render_book_entry(b, request) for b in books)
    feed_xml = _build_feed(
        feed_id="recent",
        title="Son Eklenen Kitaplar",
        request=request,
        self_href="/opds/recent.xml",
        entries_xml=entries,
        is_acquisition=True,
    )
    return Response(content=feed_xml, media_type=OPDS_ACQ_MIME)


@router.get("/all.xml", response_class=Response)
async def opds_all(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Acquisition feed for all books with pagination."""
    _ensure_opds_auth(request)
    offset = (page - 1) * limit
    data = await db.get_all_books(limit=limit, offset=offset, sort="sira_asc")
    books = data.get("items", [])
    total = data.get("total", 0)

    base = str(request.base_url).rstrip("/")
    subsections = []
    if offset + limit < total:
        next_page = page + 1
        subsections.append(
            f'  <link rel="next" href="{base}/opds/all.xml?page={next_page}&amp;limit={limit}" type="{OPDS_ACQ_MIME}" title="Sonraki Sayfa" />'
        )
    if page > 1:
        prev_page = page - 1
        subsections.append(
            f'  <link rel="previous" href="{base}/opds/all.xml?page={prev_page}&amp;limit={limit}" type="{OPDS_ACQ_MIME}" title="Önceki Sayfa" />'
        )

    entries = "\n".join(_render_book_entry(b, request) for b in books)
    feed_xml = _build_feed(
        feed_id=f"all:p{page}",
        title=f"Tüm Kitaplar (Sayfa {page})",
        request=request,
        self_href=f"/opds/all.xml?page={page}&limit={limit}",
        entries_xml=entries,
        subsections_xml="\n".join(subsections),
        is_acquisition=True,
    )
    return Response(content=feed_xml, media_type=OPDS_ACQ_MIME)


@router.get("/favorites.xml", response_class=Response)
async def opds_favorites(request: Request, db: DatabaseManager = Depends(get_db)) -> Response:
    """Acquisition feed for favorite books."""
    _ensure_opds_auth(request)
    data = await db.get_all_books(limit=100, offset=0, favorite=True, sort="title_asc")
    books = data.get("items", [])

    entries = "\n".join(_render_book_entry(b, request) for b in books)
    feed_xml = _build_feed(
        feed_id="favorites",
        title="Favori Kitaplarım",
        request=request,
        self_href="/opds/favorites.xml",
        entries_xml=entries,
        is_acquisition=True,
    )
    return Response(content=feed_xml, media_type=OPDS_ACQ_MIME)


@router.get("/categories.xml", response_class=Response)
async def opds_categories(request: Request, db: DatabaseManager = Depends(get_db)) -> Response:
    """Navigation feed for categories."""
    _ensure_opds_auth(request)
    base = str(request.base_url).rstrip("/")
    stats = await db.get_stats()
    categories = stats.get("categories", [])

    entries = []
    for cat in categories:
        cat_name = cat.get("name") or "Genel"
        count = cat.get("count", 0)
        safe_encoded = quote(cat_name)
        cat_url = f"{base}/opds/category/{safe_encoded}.xml"
        entries.append(f"""  <entry>
    <title>{_xml_escape(cat_name)} ({count})</title>
    <id>urn:dijital-kutuphane:opds:cat:{quote(cat_name)}</id>
    <updated>{_format_iso()}</updated>
    <content type="text">{count} adet kitap</content>
    <link rel="subsection" href="{cat_url}" type="{OPDS_ACQ_MIME}" />
  </entry>""")

    feed_xml = _build_feed(
        feed_id="categories",
        title="Kategoriler",
        request=request,
        self_href="/opds/categories.xml",
        entries_xml="\n".join(entries),
        is_acquisition=False,
    )
    return Response(content=feed_xml, media_type=OPDS_NAV_MIME)


@router.get("/category/{cat_name}.xml", response_class=Response)
async def opds_category_books(
    cat_name: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Acquisition feed for books in a specific category."""
    _ensure_opds_auth(request)
    raw_cat = unquote(cat_name)
    data = await db.get_all_books(limit=100, category=raw_cat, sort="title_asc")
    books = data.get("items", [])

    entries = "\n".join(_render_book_entry(b, request) for b in books)
    feed_xml = _build_feed(
        feed_id=f"category:{quote(raw_cat)}",
        title=f"Kategori: {raw_cat}",
        request=request,
        self_href=f"/opds/category/{quote(raw_cat)}.xml",
        entries_xml=entries,
        is_acquisition=True,
    )
    return Response(content=feed_xml, media_type=OPDS_ACQ_MIME)


@router.get("/collections.xml", response_class=Response)
async def opds_collections(request: Request, db: DatabaseManager = Depends(get_db)) -> Response:
    """Navigation feed for user collections."""
    _ensure_opds_auth(request)
    base = str(request.base_url).rstrip("/")
    collections = await db.get_collections()

    entries = []
    for col in collections:
        col_id = col["id"]
        col_name = col["isim"]
        col_url = f"{base}/opds/collection/{col_id}.xml"
        entries.append(f"""  <entry>
    <title>{_xml_escape(col_name)}</title>
    <id>urn:dijital-kutuphane:opds:col:{col_id}</id>
    <updated>{_format_iso()}</updated>
    <content type="text">Özel koleksiyon listesi</content>
    <link rel="subsection" href="{col_url}" type="{OPDS_ACQ_MIME}" />
  </entry>""")

    feed_xml = _build_feed(
        feed_id="collections",
        title="Koleksiyonlar",
        request=request,
        self_href="/opds/collections.xml",
        entries_xml="\n".join(entries),
        is_acquisition=False,
    )
    return Response(content=feed_xml, media_type=OPDS_NAV_MIME)


@router.get(
    "/collection/{col_id}.xml",
    response_class=Response,
    responses={
        401: {"description": "OPDS Authentication Required"},
        404: {"description": "Collection not found"},
    },
)
async def opds_collection_books(
    col_id: int,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Acquisition feed for books inside a collection."""
    _ensure_opds_auth(request)
    col_name = await db.get_collection_name(col_id)
    if not col_name:
        raise HTTPException(status_code=404, detail="Collection not found")

    books = await db.get_collection_books(col_id)
    entries = "\n".join(_render_book_entry(b, request) for b in books)
    feed_xml = _build_feed(
        feed_id=f"collection:{col_id}",
        title=f"Koleksiyon: {col_name}",
        request=request,
        self_href=f"/opds/collection/{col_id}.xml",
        entries_xml=entries,
        is_acquisition=True,
    )
    return Response(content=feed_xml, media_type=OPDS_ACQ_MIME)


@router.get("/opensearch.xml", response_class=Response)
async def opds_opensearch(request: Request) -> Response:
    """OpenSearch 1.1 description document for OPDS client search discovery."""
    _ensure_opds_auth(request)
    base = str(request.base_url).rstrip("/")
    template_url = f"{base}/opds/search.xml?q={{searchTerms}}"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>Dijital Kütüphane</ShortName>
  <Description>Dijital Kütüphanede Kitap Arayın</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <OutputEncoding>UTF-8</OutputEncoding>
  <Url type="{OPDS_ACQ_MIME}" template="{template_url}" />
</OpenSearchDescription>"""
    return Response(content=xml.strip(), media_type=OPENSEARCH_MIME)


@router.get("/search.xml", response_class=Response)
async def opds_search(
    request: Request,
    q: str = Query("", alias="q"),
    db: DatabaseManager = Depends(get_db),
) -> Response:
    """Acquisition feed for search queries."""
    _ensure_opds_auth(request)
    query = q.strip()
    if query:
        data = await db.get_all_books(limit=50, search=query, sort="sira_asc")
        books = data.get("items", [])
    else:
        books = []

    entries = "\n".join(_render_book_entry(b, request) for b in books)
    feed_xml = _build_feed(
        feed_id=f"search:{quote(query)}",
        title=f"Arama Sonuçları: {query}" if query else "Arama Sonuçları",
        request=request,
        self_href=f"/opds/search.xml?q={quote(query)}",
        entries_xml=entries,
        is_acquisition=True,
    )
    return Response(content=feed_xml, media_type=OPDS_ACQ_MIME)


@router.get(
    "/download/{file_hash}",
    responses={
        401: {"description": "OPDS Authentication Required"},
        403: {"description": "Erişim reddedildi"},
        404: {"description": "Kitap veya kitap dosyası bulunamadı"},
    },
)
async def opds_download_book(
    file_hash: str,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> FileResponse:
    """Direct book acquisition download stream for e-readers."""
    file_hash = validate_file_hash(file_hash)
    _ensure_opds_auth(request)

    row = await db.get_book_path(file_hash)
    if not row:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı")

    doc_path = row[0]
    doc_name = row[1] or "kitap"

    from app.constants import LIBRARY_ROOT

    if not is_path_within(LIBRARY_ROOT, doc_path):
        log_event("security", "WARNING", f"OPDS Path traversal attempt: {doc_path}")
        raise HTTPException(status_code=403, detail="Erişim reddedildi")

    if not os.path.exists(doc_path):
        log_event("filesystem", "ERROR", f"OPDS Book file not found on disk: {doc_path}")
        raise HTTPException(status_code=404, detail="Kitap dosyası diskte bulunamadı")

    lower_name = doc_name.lower()
    if lower_name.endswith(".epub"):
        media_type = MIME_EPUB
    elif lower_name.endswith(".txt"):
        media_type = MIME_TXT
    else:
        media_type = MIME_PDF
    safe_name = quote(doc_name)

    return FileResponse(
        path=doc_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}",
            "Accept-Ranges": "bytes",
        },
    )


@router.get(
    "/cover/{file_hash}",
    responses={
        401: {"description": "OPDS Authentication Required"},
        404: {"description": "Cover not available"},
    },
)
async def opds_cover_image(
    file_hash: str,
    request: Request,
) -> Response:
    """Serve cover thumbnail for OPDS feed entries."""
    _ensure_opds_auth(request)
    file_hash = validate_file_hash(file_hash)
    thumb_path = os.path.join(THUMBNAILS_DIR, f"{file_hash}.jpg")

    if os.path.exists(thumb_path):
        return FileResponse(
            thumb_path,
            media_type=MIME_JPEG,
            headers={"Cache-Control": "public, max-age=86400"},
        )

    # Fallback to generating a minimal 1x1 or default JPEG
    # Return 404 or empty image
    raise HTTPException(status_code=404, detail="Cover not available")
