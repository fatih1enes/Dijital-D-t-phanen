"""Hybrid Search Engine combining SQLite FTS5 (BM25) and Vector Search with RRF."""

import asyncio
import html
import re
from typing import Any

import numpy as np

from app.database import DatabaseManager
from app.logger import log_event
from app.services.embedding_service import (
    cosine_similarity,
    deserialize_vector,
    embedding_service,
)


def _clean_fts5_query(query: str) -> str:
    """Sanitize user query for SQLite FTS5 full-text matching."""
    # Remove FTS5 control characters (*, ", :, ^, OR, NOT, AND)
    cleaned = re.sub(r"[^\w\s]", " ", query, flags=re.UNICODE)
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1]
    if not tokens:
        return ""
    # Combine tokens with OR or implicit MATCH
    return " OR ".join(f'"{t}"' for t in tokens)


class HybridSearchEngine:
    """Combines BM25 lexical keyword matching and dense vector semantic similarity using RRF."""

    @staticmethod
    async def search_bm25(
        db: DatabaseManager,
        query: str,
        file_hash: str | None = None,
        exclude_hash: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Perform BM25 full-text keyword search on kitap_chunks_fts."""
        fts_query = _clean_fts5_query(query)
        if not fts_query:
            return []

        try:
            sql = """
                SELECT rowid, dosya_hash, sayfa_no, chunk_index, metin, bm25(kitap_chunks_fts) as rank
                FROM kitap_chunks_fts
                WHERE kitap_chunks_fts MATCH ?
            """
            params: list[Any] = [fts_query]

            if file_hash:
                sql += " AND dosya_hash = ?"
                params.append(file_hash)
            elif exclude_hash:
                sql += " AND dosya_hash != ?"
                params.append(exclude_hash)

            sql += " ORDER BY rank ASC LIMIT ?"
            params.append(limit)

            cursor = await db.conn.execute(sql, params)
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                results.append(
                    {
                        "id": r[0],
                        "dosya_hash": r[1],
                        "sayfa_no": r[2],
                        "chunk_index": r[3],
                        "metin": r[4],
                        "bm25_score": abs(float(r[5])),
                    }
                )
            return results
        except Exception as e:
            log_event("database", "WARNING", f"BM25 FTS5 arama uyarısı: {e}")
            return []

    @staticmethod
    async def deep_search_pages(
        db: DatabaseManager,
        query: str,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """Perform deep page-level BM25 search across all book chunks in the library.

        Returns highlighted snippets, exact page numbers, book titles, and hashes
        for instant 1-click teleportation to the exact page in the PDF reader.
        """
        fts_query = _clean_fts5_query(query)
        if not fts_query:
            return []

        try:
            sql = """
                SELECT
                    fts.dosya_hash,
                    fts.sayfa_no,
                    fts.chunk_index,
                    snippet(kitap_chunks_fts, 3, '\x01', '\x02', ' … ', 24) AS snippet_text,
                    bm25(kitap_chunks_fts) AS bm25_rank,
                    COALESCE(k.kitap_adi, k.dosya_adi, 'İsimsiz') AS kitap_adi,
                    COALESCE(k.yazar, 'Bilinmiyor') AS yazar,
                    k.kategori,
                    k.has_cover
                FROM kitap_chunks_fts fts
                JOIN kitaplar k ON k.dosya_hash = fts.dosya_hash
                WHERE kitap_chunks_fts MATCH ?
                ORDER BY bm25_rank ASC
                LIMIT ?
            """
            cursor = await db.conn.execute(sql, (fts_query, limit))
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                raw_snip = html.escape(r[3] or "")
                safe_snip = raw_snip.replace("\x01", '<mark class="deep-hl">').replace("\x02", "</mark>")
                results.append(
                    {
                        "dosya_hash": r[0],
                        "sayfa_no": r[1],
                        "chunk_index": r[2],
                        "snippet": safe_snip,
                        "rank": abs(float(r[4])),
                        "kitap_adi": r[5],
                        "yazar": r[6],
                        "kategori": r[7],
                        "has_cover": bool(r[8]),
                    }
                )
            return results
        except Exception as e:
            log_event("database", "WARNING", f"Deep search hatası: {e}")
            return []

    @staticmethod
    async def search_vector(
        db: DatabaseManager,
        query_vector: list[float],
        file_hash: str | None = None,
        exclude_hash: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Perform in-process vector cosine similarity search over stored chunk embeddings."""
        if not query_vector:
            return []

        try:
            sql = "SELECT id, dosya_hash, sayfa_no, chunk_index, metin, embedding FROM kitap_chunks WHERE embedding IS NOT NULL"
            params: list[Any] = []

            if file_hash:
                sql += " AND dosya_hash = ?"
                params.append(file_hash)
            elif exclude_hash:
                sql += " AND dosya_hash != ?"
                params.append(exclude_hash)

            cursor = await db.conn.execute(sql, params)
            rows = await cursor.fetchall()
            if not rows:
                return []

            def _score_rows_vectorized() -> list[dict[str, Any]]:
                q_arr = np.asarray(query_vector, dtype=np.float32)
                q_norm = float(np.linalg.norm(q_arr))
                if q_norm < 1e-12:
                    return []
                q_unit = q_arr / q_norm
                dim = len(q_unit)

                valid_rows = []
                blobs = []
                fallback_scored: list[dict[str, Any]] = []
                expected_bytes = dim * 4

                for r in rows:
                    emb_blob = r[5]
                    if not emb_blob:
                        continue
                    if len(emb_blob) == expected_bytes:
                        valid_rows.append(r)
                        blobs.append(np.frombuffer(emb_blob, dtype=np.float32))
                    else:
                        vec = deserialize_vector(emb_blob)
                        if len(vec) == dim:
                            sim = cosine_similarity(q_unit, vec)
                            fallback_scored.append(
                                {
                                    "id": r[0],
                                    "dosya_hash": r[1],
                                    "sayfa_no": r[2],
                                    "chunk_index": r[3],
                                    "metin": r[4],
                                    "vector_score": sim,
                                }
                            )

                scored: list[dict[str, Any]] = list(fallback_scored)
                if blobs:
                    mat = np.vstack(blobs)
                    norms = np.linalg.norm(mat, axis=1)
                    safe_norms = np.where(norms < 1e-12, 1.0, norms)
                    sims = (mat @ q_unit) / safe_norms
                    sims = np.where(norms < 1e-12, 0.0, sims)
                    for r, sim_val in zip(valid_rows, sims.tolist(), strict=False):
                        scored.append(
                            {
                                "id": r[0],
                                "dosya_hash": r[1],
                                "sayfa_no": r[2],
                                "chunk_index": r[3],
                                "metin": r[4],
                                "vector_score": float(sim_val),
                            }
                        )

                scored.sort(key=lambda x: x["vector_score"], reverse=True)
                return scored[:limit]

            return await asyncio.to_thread(_score_rows_vectorized)
        except Exception as e:
            log_event("database", "WARNING", f"Vektör arama uyarısı: {e}")
            return []

    @classmethod
    async def hybrid_search(
        cls,
        db: DatabaseManager,
        query: str,
        file_hash: str | None = None,
        exclude_hash: str | None = None,
        limit: int = 5,
        rrf_k: int = 60,
    ) -> list[dict[str, Any]]:
        """Combine BM25 and Vector search results using Reciprocal Rank Fusion (RRF).

        RRF formula: score = sum(1.0 / (k + rank))
        """
        if not query or not query.strip():
            return []

        # 1. BM25 Lexical retrieval
        bm25_candidates = await cls.search_bm25(
            db, query, file_hash=file_hash, exclude_hash=exclude_hash, limit=limit * 3
        )

        # 2. Vector Semantic retrieval
        query_vec = embedding_service.generate_embedding(query)
        vector_candidates = await cls.search_vector(
            db,
            query_vec,
            file_hash=file_hash,
            exclude_hash=exclude_hash,
            limit=limit * 3,
        )

        # 3. Fuse scores via RRF
        combined: dict[str, dict[str, Any]] = {}

        # Add BM25 ranks
        for rank, item in enumerate(bm25_candidates):
            key = f"{item['dosya_hash']}_{item['sayfa_no']}_{item['chunk_index']}"
            if key not in combined:
                combined[key] = {
                    "dosya_hash": item["dosya_hash"],
                    "sayfa_no": item["sayfa_no"],
                    "chunk_index": item["chunk_index"],
                    "metin": item["metin"],
                    "rrf_score": 0.0,
                    "bm25_rank": rank + 1,
                    "vector_score": 0.0,
                }
            combined[key]["rrf_score"] += 1.0 / (rrf_k + rank + 1)

        # Add Vector ranks
        for rank, item in enumerate(vector_candidates):
            key = f"{item['dosya_hash']}_{item['sayfa_no']}_{item['chunk_index']}"
            if key not in combined:
                combined[key] = {
                    "dosya_hash": item["dosya_hash"],
                    "sayfa_no": item["sayfa_no"],
                    "chunk_index": item["chunk_index"],
                    "metin": item["metin"],
                    "rrf_score": 0.0,
                    "bm25_rank": None,
                    "vector_score": item.get("vector_score", 0.0),
                }
            combined[key]["vector_score"] = item.get("vector_score", 0.0)
            combined[key]["rrf_score"] += 1.0 / (rrf_k + rank + 1)

        # Sort combined results by RRF score descending
        fused = sorted(combined.values(), key=lambda x: x["rrf_score"], reverse=True)
        return fused[:limit]


# Global instance
hybrid_search_engine = HybridSearchEngine()
