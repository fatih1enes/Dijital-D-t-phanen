"""Dialectic Multi-Agent Debate, Knowledge Graph, and Serendipity endpoints router."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from app.auth import _ensure_authorized
from app.config import is_real_api_key, load_config, resolve_ai_credentials
from app.database import DatabaseManager
from app.dependencies import get_db
from app.logger import log_event
from app.models import DebateRequest, EntityUpsertRequest, RelationCreateRequest
from app.services.knowledge_graph import knowledge_graph_service
from app.services.multi_agent_debate import multi_agent_debate_engine
from app.services.serendipity_engine import serendipity_engine
from app.utils import validate_file_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["debate", "knowledge_graph", "serendipity"])


# --------------------------------------------------------------------------
# Multi-Agent Debate Endpoints
# --------------------------------------------------------------------------


@router.post(
    "/debate",
    responses={
        400: {"description": "Geçersiz istek"},
        500: {"description": "Sunucu hatası"},
    },
)
@router.post(
    "/ai/debate",
    responses={
        400: {"description": "Geçersiz istek"},
        500: {"description": "Sunucu hatası"},
    },
)
async def debate_endpoint(
    request: DebateRequest,
    http_request: Request,
    x_ai_provider: str | None = Header(None),
    x_ai_key: str | None = Header(None),
    x_ai_model: str | None = Header(None, alias="X-AI-Model"),
    x_ai_model_name: str | None = Header(None, alias="X-AI-Model-Name"),
    x_ai_base_url: str | None = Header(None, alias="X-AI-Base-Url"),
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Execute dialectic debate between two or more books with grounded [Sayfa X] citations."""
    _ensure_authorized(http_request)

    # Validate book hashes
    validated_hashes: list[str] = []
    for h in request.book_hashes:
        validated_hashes.append(validate_file_hash(h))

    cfg = load_config()
    provider, api_key, model_name, base_url = resolve_ai_credentials(
        provider=x_ai_provider,
        api_key=x_ai_key,
        model=x_ai_model_name or x_ai_model,
        base_url=x_ai_base_url,
        cfg=cfg,
        is_key_fn=is_real_api_key,
    )

    try:
        result = await multi_agent_debate_engine.conduct_debate(
            db=db,
            book_hashes=validated_hashes,
            topic=request.topic,
            rounds=request.rounds,
            provider=provider,
            api_key=api_key,
            model=model_name,
            base_url=base_url,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as exc:
        log_event("ai", "ERROR", f"Diyalektik tartışma çalıştırma hatası: {exc}")
        raise HTTPException(status_code=500, detail=f"Tartışma motoru hatası: {exc}") from exc


# --------------------------------------------------------------------------
# Smart Serendipity Endpoints
# --------------------------------------------------------------------------


@router.get("/books/{file_hash}/serendipity")
async def get_book_serendipity(
    file_hash: str,
    http_request: Request,
    text: str = Query(default="", description="İlişkili kavram veya aktif pasaj metni"),
    limit: int = Query(default=5, ge=1, le=20),
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Discover serendipitous conceptual links and citations across other books in the library."""
    _ensure_authorized(http_request)
    valid_hash = validate_file_hash(file_hash)

    # If query text is empty, check if book has a summary or active keywords to search against
    query_str = text.strip()
    if not query_str:
        book = await db.get_book_by_hash(valid_hash)
        if book:
            query_str = (
                book.get("anahtar_kelimeler") or book.get("ozet") or book.get("kitap_adi") or ""
            )

    return await serendipity_engine.find_connections(
        db=db, current_book_hash=valid_hash, query_text=query_str, limit=limit
    )


# --------------------------------------------------------------------------
# Knowledge Graph Endpoints
# --------------------------------------------------------------------------


@router.get("/graph/stats")
async def get_graph_statistics(
    http_request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Get total entity and relation count metrics from SQLite Knowledge Graph."""
    _ensure_authorized(http_request)
    return await knowledge_graph_service.get_graph_stats(db)


@router.get("/graph/search")
async def search_graph_entities(
    http_request: Request,
    q: str = Query(default="", description="Varlık arama terimi"),
    type: str | None = Query(
        default=None,
        description="Varlık tipi filtresi (book, author, category, concept)",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Search knowledge graph entities."""
    _ensure_authorized(http_request)
    entities = await knowledge_graph_service.search_entities(
        db, query=q, entity_type=type, limit=limit
    )
    return {"items": entities, "count": len(entities)}


@router.get("/graph/neighbors/{entity_id}")
async def get_graph_neighbors(
    entity_id: str,
    http_request: Request,
    max_depth: int = Query(default=2, ge=1, le=4),
    limit: int = Query(default=50, ge=1, le=200),
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Traverse graph neighborhood up to max_depth using Recursive CTE."""
    _ensure_authorized(http_request)
    return await knowledge_graph_service.get_neighborhood(
        db=db, entity_id=entity_id, max_depth=max_depth, limit=limit
    )


@router.get("/graph/path")
async def get_graph_path(
    source: str,
    target: str,
    http_request: Request,
    max_depth: int = Query(default=4, ge=1, le=6),
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Find shortest relationship path between two entities using Recursive CTE."""
    _ensure_authorized(http_request)
    path = await knowledge_graph_service.find_path(
        db=db, source_id=source, target_id=target, max_depth=max_depth
    )
    return {"source": source, "target": target, "path": path, "found": len(path) > 0}


@router.post("/graph/entities")
async def upsert_graph_entity(
    request: EntityUpsertRequest,
    http_request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Create or update an entity node in the knowledge graph."""
    _ensure_authorized(http_request)
    return await knowledge_graph_service.upsert_entity(
        db=db,
        entity_id=request.id,
        name=request.name,
        entity_type=request.entity_type,
        description=request.description,
        metadata=request.metadata,
    )


@router.post("/graph/relations")
async def create_graph_relation(
    request: RelationCreateRequest,
    http_request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Create a directed relation edge between two entities."""
    _ensure_authorized(http_request)
    rel_id = await knowledge_graph_service.add_relation(
        db=db,
        source_id=request.source_id,
        relation_type=request.relation_type,
        target_id=request.target_id,
        weight=request.weight,
        source_evidence=request.source_evidence,
    )
    return {"id": rel_id, "success": True}


@router.post(
    "/graph/index-book/{file_hash}",
    responses={404: {"description": "Kitap bulunamadı"}},
)
async def index_book_to_graph(
    file_hash: str,
    http_request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Extract and index a book's metadata and user notes into the Knowledge Graph."""
    _ensure_authorized(http_request)
    valid_hash = validate_file_hash(file_hash)
    book = await db.get_book_by_hash(valid_hash)
    if not book:
        raise HTTPException(status_code=404, detail="Kitap bulunamadı")

    meta_stats = await knowledge_graph_service.index_book(db, dict(book))
    note_stats = await knowledge_graph_service.index_notes_for_book(db, valid_hash)

    return {
        "book_hash": valid_hash,
        "metadata_indexed": meta_stats,
        "notes_indexed": note_stats,
        "success": True,
    }
