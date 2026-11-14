"""Tests for Phase 3: Chunking Service, Embedding Service, and Hybrid RAG Search (FTS5 + Vector + RRF)."""

import pytest

from app.services.chunking_service import (
    DocumentChunker,
    _split_text_into_chunks,
    index_document_chunks,
)
from app.services.embedding_service import (
    cosine_similarity,
    deserialize_vector,
    embedding_service,
    normalize_vector,
    serialize_vector,
)
from app.services.hybrid_search import (
    _clean_fts5_query,
    hybrid_search_engine,
)


class TestChunkingService:
    """Validate document text chunking and page index tracking."""

    def test_split_text_into_chunks(self):
        sample = (
            "Birinci paragraf metni burada yer almaktadır.\n\n"
            "İkinci paragraf felsefi temelleri ve mantıksal argümanları ele alır. "
            "Bu argümanlar bilginin kaynağını sorgular.\n\n"
            "Üçüncü paragraf ise metodolojik yaklaşımları özetler."
        )
        chunks = _split_text_into_chunks(sample, max_chars=120, overlap_chars=20)
        assert len(chunks) >= 2
        for c in chunks:
            assert len(c) <= 150  # Boundary buffer

    def test_chunk_txt_virtual_pages(self, tmp_path):
        txt_file = tmp_path / "deneme.txt"
        content = "Felsefe ve mantık üzerine denemeler.\n" * 150  # ~5400 chars
        txt_file.write_text(content, encoding="utf-8")

        chunks = DocumentChunker.chunk_document(
            str(txt_file), file_hash="txt_hash_1", max_chars=400
        )
        assert len(chunks) > 0
        assert all(c["dosya_hash"] == "txt_hash_1" for c in chunks)
        # Verify page progression (1, 2, 3...)
        pages = {c["sayfa_no"] for c in chunks}
        assert len(pages) >= 2

    @pytest.mark.asyncio
    async def test_index_document_chunks(self, temp_db):
        test_hash = "h" * 64
        await temp_db.add_book(
            {
                "dosya_hash": test_hash,
                "dosya_yolu": "/fake/p.pdf",
                "dosya_adi": "p.pdf",
                "kitap_adi": "Test Doküman",
                "has_cover": False,
            }
        )

        chunks = [
            {
                "dosya_hash": test_hash,
                "sayfa_no": 1,
                "chunk_index": 0,
                "metin": "Yapay zeka modelleri makine öğrenmesi algoritmalarına dayanır.",
                "char_count": 62,
            },
            {
                "dosya_hash": test_hash,
                "sayfa_no": 2,
                "chunk_index": 1,
                "metin": "Doğal dil işleme semantik vektör uzaylarında anlamsal yakınlık ölçer.",
                "char_count": 68,
            },
        ]
        embeddings = [embedding_service.generate_embedding_blob(c["metin"]) for c in chunks]

        saved_count = await index_document_chunks(temp_db, chunks, embeddings)
        assert saved_count == 2

        # Verify in SQLite tables
        cur = await temp_db.conn.execute(
            "SELECT count(*) FROM kitap_chunks WHERE dosya_hash = ?", (test_hash,)
        )
        assert (await cur.fetchone())[0] == 2

        cur_fts = await temp_db.conn.execute(
            "SELECT count(*) FROM kitap_chunks_fts WHERE dosya_hash = ?", (test_hash,)
        )
        assert (await cur_fts.fetchone())[0] == 2


class TestEmbeddingService:
    """Validate vector mathematics, normalization, and serialization."""

    def test_serialize_deserialize_roundtrip(self):
        vec = [0.1234, -0.5678, 0.9999, -1.0, 0.0]
        blob = serialize_vector(vec)
        assert isinstance(blob, bytes)
        assert len(blob) == len(vec) * 4  # 4 bytes per float32

        recovered = deserialize_vector(blob)
        assert len(recovered) == len(vec)
        for orig, rec in zip(vec, recovered, strict=True):
            assert abs(orig - rec) < 1e-4

    def test_normalize_vector(self):
        vec = [3.0, 4.0]  # Norm is 5.0
        normalized = normalize_vector(vec)
        assert abs(normalized[0] - 0.6) < 1e-5
        assert abs(normalized[1] - 0.8) < 1e-5

    def test_cosine_similarity(self):
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        vec_c = [0.0, 1.0, 0.0]
        vec_d = [-1.0, 0.0, 0.0]

        assert abs(cosine_similarity(vec_a, vec_b) - 1.0) < 1e-5  # Identical
        assert abs(cosine_similarity(vec_a, vec_c) - 0.0) < 1e-5  # Orthogonal
        assert abs(cosine_similarity(vec_a, vec_d) - (-1.0)) < 1e-5  # Opposite

    def test_deterministic_embedding_generation(self):
        text = "Felsefe ve epistemoloji araştırmaları"
        emb1 = embedding_service.generate_embedding(text)
        emb2 = embedding_service.generate_embedding(text)
        assert emb1 == emb2
        assert len(emb1) == 384

        diff_text = "Farklı bir konu kuantum fiziği"
        emb_diff = embedding_service.generate_embedding(diff_text)
        assert emb1 != emb_diff


class TestHybridSearchEngine:
    """Validate FTS5 BM25, Vector Search, and Reciprocal Rank Fusion."""

    @pytest.fixture(autouse=True)
    async def populate_search_data(self, temp_db):
        self.hash_1 = "1" * 64
        self.hash_2 = "2" * 64

        await temp_db.add_book(
            {
                "dosya_hash": self.hash_1,
                "dosya_yolu": "/p1.pdf",
                "dosya_adi": "p1.pdf",
                "kitap_adi": "Yapay Zeka ve Felsefe",
                "has_cover": False,
            }
        )
        await temp_db.add_book(
            {
                "dosya_hash": self.hash_2,
                "dosya_yolu": "/p2.pdf",
                "dosya_adi": "p2.pdf",
                "kitap_adi": "Astronomi ve Uzay",
                "has_cover": False,
            }
        )

        chunks = [
            {
                "dosya_hash": self.hash_1,
                "sayfa_no": 12,
                "chunk_index": 0,
                "metin": "Turing testi, makinelerin insan düzeyinde akıllı davranış sergileme yeteneğini ölçer.",
                "char_count": 85,
            },
            {
                "dosya_hash": self.hash_1,
                "sayfa_no": 45,
                "chunk_index": 1,
                "metin": "Bilinç ve zihin felsefesi epistemolojik çıkarımlarla açıklanır.",
                "char_count": 62,
            },
            {
                "dosya_hash": self.hash_2,
                "sayfa_no": 101,
                "chunk_index": 2,
                "metin": "Güneş sistemi ve gezegenlerin yörüngeleri yerçekimi kanunlarına uyar.",
                "char_count": 67,
            },
        ]
        embeddings = [embedding_service.generate_embedding_blob(c["metin"]) for c in chunks]
        await index_document_chunks(temp_db, chunks, embeddings)

    @pytest.mark.asyncio
    async def test_search_bm25(self, temp_db):
        results = await hybrid_search_engine.search_bm25(temp_db, "Turing testi", limit=5)
        assert len(results) >= 1
        assert results[0]["dosya_hash"] == self.hash_1
        assert results[0]["sayfa_no"] == 12

    @pytest.mark.asyncio
    async def test_search_vector(self, temp_db):
        query_vec = embedding_service.generate_embedding("gezegenler ve güneş sistemi")
        results = await hybrid_search_engine.search_vector(temp_db, query_vec, limit=5)
        assert len(results) >= 1
        assert results[0]["dosya_hash"] == self.hash_2
        assert results[0]["sayfa_no"] == 101

    @pytest.mark.asyncio
    async def test_hybrid_search_rrf(self, temp_db):
        results = await hybrid_search_engine.hybrid_search(
            temp_db, "Turing akıllı makineler", limit=5
        )
        assert len(results) >= 1
        top = results[0]
        assert top["dosya_hash"] == self.hash_1
        assert top["sayfa_no"] == 12
        assert "rrf_score" in top
        assert top["rrf_score"] > 0

    @pytest.mark.asyncio
    async def test_hybrid_search_with_file_hash_filter(self, temp_db):
        # Even with generic query, restrict only to book 2
        results = await hybrid_search_engine.hybrid_search(
            temp_db, "kanunları sistem", file_hash=self.hash_2, limit=5
        )
        assert len(results) >= 1
        assert all(r["dosya_hash"] == self.hash_2 for r in results)


class TestChatCitationIntegration:
    """Validate chat prompt RAG passage injection and citation formatting."""

    @pytest.mark.asyncio
    async def test_build_target_book_context_with_hybrid_rag(self, temp_db):
        from app.routers.chat import _build_target_book_context

        test_hash = "3" * 64
        await temp_db.add_book(
            {
                "dosya_hash": test_hash,
                "dosya_yolu": "/p3.pdf",
                "dosya_adi": "p3.pdf",
                "kitap_adi": "Kritik Düşünce",
                "yazar": "Filozof",
                "ozet": "Mantık ve düşünme sanatı.",
                "has_cover": False,
            }
        )
        chunks = [
            {
                "dosya_hash": test_hash,
                "sayfa_no": 84,
                "chunk_index": 0,
                "metin": "Argüman geçerliliği öncüllerin doğru olması durumunda sonucun zorunlu çıkmasıdır.",
                "char_count": 80,
            }
        ]
        embeddings = [embedding_service.generate_embedding_blob(c["metin"]) for c in chunks]
        await index_document_chunks(temp_db, chunks, embeddings)

        meta, rag_ctx, pdf = await _build_target_book_context(
            temp_db, test_hash, provider="ollama", user_query="Argüman geçerliliği nedir?"
        )
        assert meta["title"] == "Kritik Düşünce"
        assert "[Sayfa 84]" in rag_ctx
        assert "Argüman geçerliliği" in rag_ctx

    def test_clean_fts5_query_sanitization(self):
        raw = 'Yapay zeka: "makine öğrenmesi" & test* ^123'
        cleaned = _clean_fts5_query(raw)
        assert '"Yapay"' in cleaned
        assert '"zeka"' in cleaned
        assert '"makine"' in cleaned
        # Special characters stripped
        assert "*" not in cleaned
        assert "^" not in cleaned
