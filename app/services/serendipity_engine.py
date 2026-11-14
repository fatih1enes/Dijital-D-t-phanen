"""Smart Serendipity Engine for unexpected conceptual cross-book discoveries and unlinked mentions."""

import logging
from typing import Any

from app.database import DatabaseManager
from app.logger import log_event
from app.services.hybrid_search import hybrid_search_engine
from app.services.knowledge_graph import knowledge_graph_service

logger = logging.getLogger(__name__)


class SerendipityEngine:
    """Discovers serendipitous connections between the currently active reading passage and the rest of the library."""

    @classmethod
    async def _find_cross_book_passages(
        cls, db: DatabaseManager, clean_text: str, current_book_hash: str, limit: int
    ) -> list[dict[str, Any]]:
        raw_passages = await hybrid_search_engine.hybrid_search(
            db, query=clean_text, exclude_hash=current_book_hash, limit=limit
        )
        if not raw_passages:
            return []

        hashes = list({p["dosya_hash"] for p in raw_passages})
        placeholders = ",".join("?" for _ in hashes)
        cur = await db.conn.execute(
            f"SELECT dosya_hash, kitap_adi, yazar, kategori, has_cover FROM kitaplar WHERE dosya_hash IN ({placeholders})",
            hashes,
        )
        meta_map = {
            r[0]: {
                "baslik": r[1] or "İsimsiz Kitap",
                "yazar": r[2] or "Bilinmeyen Yazar",
                "kategori": r[3] or "",
                "has_cover": bool(r[4]),
            }
            for r in await cur.fetchall()
        }

        passages: list[dict[str, Any]] = []
        for p in raw_passages:
            b_meta = meta_map.get(p["dosya_hash"], {})
            passages.append(
                {
                    "dosya_hash": p["dosya_hash"],
                    "kitap_baslik": b_meta.get("baslik", ""),
                    "kitap_yazar": b_meta.get("yazar", ""),
                    "kategori": b_meta.get("kategori", ""),
                    "sayfa_no": p["sayfa_no"],
                    "chunk_index": p["chunk_index"],
                    "metin": p["metin"],
                    "rrf_score": round(p.get("rrf_score", 0.0), 4),
                    "vector_score": round(p.get("vector_score", 0.0), 4),
                    "bm25_rank": p.get("bm25_rank"),
                }
            )
        return passages

    @classmethod
    async def _find_related_notes(
        cls, db: DatabaseManager, clean_text: str, current_book_hash: str, limit: int
    ) -> list[dict[str, Any]]:
        tokens = [t.strip() for t in clean_text.split() if len(t.strip()) > 2]
        if not tokens:
            return []

        clauses = []
        params: list[Any] = [current_book_hash]
        for tok in tokens[:4]:
            clauses.append("(n.secilen_metin LIKE ? OR n.not_metni LIKE ?)")
            pat = f"%{tok}%"
            params.extend([pat, pat])
        where_sub = " OR ".join(clauses)
        note_sql = f"""
            SELECT n.id, n.dosya_hash, n.sayfa_no, n.secilen_metin, n.not_metni, k.kitap_adi, k.yazar
            FROM kitap_notlari n
            JOIN kitaplar k ON k.dosya_hash = n.dosya_hash
            WHERE n.dosya_hash != ?
              AND ({where_sub})
            ORDER BY n.olusturma_tarihi DESC
            LIMIT ?
        """
        params.append(limit)
        cursor = await db.conn.execute(note_sql, params)
        note_rows = await cursor.fetchall()
        return [
            {
                "note_id": r[0],
                "dosya_hash": r[1],
                "sayfa_no": r[2],
                "secilen_metin": r[3] or "",
                "not_metni": r[4] or "",
                "kitap_baslik": r[5] or "",
                "kitap_yazar": r[6] or "",
            }
            for r in note_rows
        ]

    @classmethod
    async def _find_graph_connections(
        cls, db: DatabaseManager, current_book_hash: str
    ) -> list[dict[str, Any]]:
        graph_links: list[dict[str, Any]] = []
        try:
            current_entity_id = f"book:{current_book_hash}"
            neighborhood = await knowledge_graph_service.get_neighborhood(
                db, entity_id=current_entity_id, max_depth=2, limit=20
            )
            for node in neighborhood.get("nodes", []):
                nid = node.get("id", "")
                if nid != current_entity_id:
                    graph_links.append(
                        {
                            "id": nid,
                            "name": node.get("name", ""),
                            "type": node.get("entity_type", ""),
                            "depth": node.get("depth", 1),
                            "description": node.get("description", ""),
                        }
                    )
        except Exception as err:
            logger.debug("Serendipity graph traversal notice: %s", err)
        return graph_links

    @classmethod
    async def find_connections(
        cls,
        db: DatabaseManager,
        current_book_hash: str,
        query_text: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Find related passages, notes, and graph nodes across the entire library excluding the current book."""
        clean_text = (query_text or "").strip()
        if not clean_text:
            return {
                "source_book_hash": current_book_hash,
                "query": "",
                "cross_book_passages": [],
                "related_notes": [],
                "graph_connections": [],
                "total_discovered": 0,
            }

        passages = await cls._find_cross_book_passages(db, clean_text, current_book_hash, limit)
        notes = await cls._find_related_notes(db, clean_text, current_book_hash, limit)
        graph_links = await cls._find_graph_connections(db, current_book_hash)

        total = len(passages) + len(notes) + len(graph_links)
        log_event(
            "ai",
            "INFO",
            f"Serendipity keşfi: '{clean_text[:30]}...' -> {len(passages)} pasaj, {len(notes)} not, {len(graph_links)} graf bağı",
        )

        return {
            "source_book_hash": current_book_hash,
            "query": clean_text,
            "cross_book_passages": passages,
            "related_notes": notes,
            "graph_connections": graph_links[:10],
            "total_discovered": total,
        }


# Global singleton instance
serendipity_engine = SerendipityEngine()
