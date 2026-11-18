"""Unit and integration tests for Faz 2: 3-Tier Semantic Embeddings & True SSE Chat Streaming."""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import patch

import httpx
import pytest

from app.main import app as fastapi_app
from app.services.chunking_service import index_document_chunks
from app.services.embedding_service import (
    MODEL_HASH,
    MODEL_ONNX,
    embedding_service,
    serialize_vector,
)
from app.services.hybrid_search import hybrid_search_engine


@pytest.mark.asyncio
async def test_vector_space_bucket_alignment_across_mixed_models(temp_db) -> None:
    """Ensure HybridSearchEngine scores chunks in their exact embedding_model vector space."""
    h1 = "a" * 64
    h2 = "b" * 64
    await temp_db.add_book(
        {"dosya_hash": h1, "dosya_yolu": "/a.pdf", "dosya_adi": "a.pdf", "kitap_adi": "Kitap A"}
    )
    await temp_db.add_book(
        {"dosya_hash": h2, "dosya_yolu": "/b.pdf", "dosya_adi": "b.pdf", "kitap_adi": "Kitap B"}
    )

    c1 = [
        {
            "dosya_hash": h1,
            "sayfa_no": 7,
            "chunk_index": 0,
            "metin": "Kuantum dolanıklığı ve parçacık fiziği deneyleri.",
            "char_count": 49,
        }
    ]
    c2 = [
        {
            "dosya_hash": h2,
            "sayfa_no": 19,
            "chunk_index": 0,
            "metin": "Osmanlı iktisat tarihi ve vakıf hukuku belgeleri.",
            "char_count": 49,
        }
    ]

    # Index Book A with legacy hash-v1 and Book B with active local model (ONNX or hash)
    hash_blobs = [serialize_vector(embedding_service.generate_hash_embedding(c1[0]["metin"]))]
    await index_document_chunks(temp_db, c1, embeddings=hash_blobs, embedding_model=MODEL_HASH)

    local_blobs, local_model = embedding_service.generate_semantic_embeddings_batch(
        [c2[0]["metin"]], provider="none", api_key=""
    )
    assert local_model in (MODEL_ONNX, MODEL_HASH)
    await index_document_chunks(temp_db, c2, embeddings=local_blobs, embedding_model=local_model)

    res_quantum = await hybrid_search_engine.hybrid_search(temp_db, "parçacık fiziği kuantum", limit=2)
    assert res_quantum[0]["dosya_hash"] == h1
    assert res_quantum[0]["sayfa_no"] == 7

    res_history = await hybrid_search_engine.hybrid_search(temp_db, "vakıf hukuku iktisat", limit=2)
    assert res_history[0]["dosya_hash"] == h2
    assert res_history[0]["sayfa_no"] == 19


@pytest.mark.asyncio
async def test_chat_stream_sse_wire_events_and_citations(temp_db) -> None:
    """Verify POST /api/chat/stream emits citations, session, token, and done SSE frames."""
    book_hash = "c" * 64
    await temp_db.add_book(
        {
            "dosya_hash": book_hash,
            "dosya_yolu": "/nonexistent_stream_test.pdf",
            "dosya_adi": "stream.pdf",
            "kitap_adi": "Epistemoloji El Kitabı",
            "yazar": "İbn Sina",
            "ozet": "Bilgi kuramı incelemesi.",
        }
    )
    chunks = [
        {
            "dosya_hash": book_hash,
            "sayfa_no": 33,
            "chunk_index": 0,
            "metin": "Burhan sanatı kesin öncüllerden zorunlu bilgi üretir.",
            "char_count": 53,
        }
    ]
    blobs = embedding_service.generate_embeddings_batch([chunks[0]["metin"]])
    await index_document_chunks(temp_db, chunks, embeddings=blobs)

    async def fake_stream(*_args, **_kwargs) -> AsyncIterator[str]:
        yield "Burhan yöntemi "
        yield "kesin bilgi sağlar [Sayfa 33]."

    with patch("app.services.ai_service.AIService.generate_text_stream", side_effect=fake_stream):
        transport = httpx.ASGITransport(app=fastapi_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.post(
                "/api/chat/stream",
                headers={"X-AI-Provider": "ollama"},
                json={
                    "message": "Burhan sanatı nedir?",
                    "target_book_hash": book_hash,
                    "load_full_book": False,
                },
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers.get("content-type", "")
            raw = resp.text
            assert "event: citations" in raw
            assert '"page": 33' in raw
            assert "Burhan sanatı kesin öncüllerden" in raw
            assert "event: token" in raw
            assert "kesin bilgi sağlar [Sayfa 33]." in raw
            assert "event: done" in raw
