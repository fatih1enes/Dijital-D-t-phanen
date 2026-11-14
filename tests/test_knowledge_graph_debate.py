"""Unit and Integration tests for Knowledge Graph, Multi-Agent Debate, and Smart Serendipity Engine."""

import httpx
import pytest

from app.database import DatabaseManager
from app.services.knowledge_graph import knowledge_graph_service
from app.services.multi_agent_debate import _extract_citations, multi_agent_debate_engine
from app.services.serendipity_engine import serendipity_engine


@pytest.fixture
def sample_hash_a() -> str:
    return "a" * 64


@pytest.fixture
def sample_hash_b() -> str:
    return "b" * 64


class TestKnowledgeGraphService:
    """Tests for SQLite Recursive CTE Knowledge Graph triplestore."""

    @pytest.mark.asyncio
    async def test_entity_upsert_and_fetch(self, temp_db: DatabaseManager):
        """Entity can be upserted and retrieved with JSON metadata."""
        entity = await knowledge_graph_service.upsert_entity(
            db=temp_db,
            entity_id="concept:yapay_zeka",
            name="Yapay Zekâ",
            entity_type="concept",
            description="Makinelerin öğrenme ve akıl yürütme yetisi.",
            metadata={"domain": "Computer Science", "importance": 5},
        )
        assert entity["id"] == "concept:yapay_zeka"
        assert entity["name"] == "Yapay Zekâ"

        fetched = await knowledge_graph_service.get_entity(temp_db, "concept:yapay_zeka")
        assert fetched is not None
        assert fetched["name"] == "Yapay Zekâ"
        assert fetched["metadata"].get("domain") == "Computer Science"

    @pytest.mark.asyncio
    async def test_entity_search(self, temp_db: DatabaseManager):
        """Entities can be searched by name substring and type filter."""
        await knowledge_graph_service.upsert_entity(
            temp_db, "author:kant", "Immanuel Kant", "author", "Alman Aydınlanma filozofu"
        )
        await knowledge_graph_service.upsert_entity(
            temp_db, "author:hegel", "G. W. F. Hegel", "author", "Alman İdealisti"
        )

        results = await knowledge_graph_service.search_entities(temp_db, query="Kant")
        assert len(results) == 1
        assert results[0]["name"] == "Immanuel Kant"

        authors = await knowledge_graph_service.search_entities(temp_db, entity_type="author")
        assert len(authors) == 2

    @pytest.mark.asyncio
    async def test_relation_creation_and_stats(self, temp_db: DatabaseManager):
        """Relations can be added, retrieved, and reflected in stats."""
        await knowledge_graph_service.upsert_entity(
            temp_db, "book:1", "Saf Aklın Eleştirisi", "book"
        )
        await knowledge_graph_service.upsert_entity(temp_db, "author:kant", "Kant", "author")

        rel_id = await knowledge_graph_service.add_relation(
            db=temp_db,
            source_id="book:1",
            relation_type="authored_by",
            target_id="author:kant",
            weight=1.0,
            source_evidence="Kapak bilgisi",
        )
        assert rel_id > 0

        relations = await knowledge_graph_service.get_relations(temp_db, entity_id="book:1")
        assert len(relations) == 1
        assert relations[0]["relation_type"] == "authored_by"
        assert relations[0]["target_id"] == "author:kant"

        stats = await knowledge_graph_service.get_graph_stats(temp_db)
        assert stats["total_entities"] >= 2
        assert stats["total_relations"] >= 1
        assert stats["relation_types"].get("authored_by") == 1

    @pytest.mark.asyncio
    async def test_recursive_cte_neighborhood_traversal(self, temp_db: DatabaseManager):
        """Recursive CTE correctly traverses 2-hop neighborhood and captures edges."""
        # Setup: A -> B -> C
        await knowledge_graph_service.upsert_entity(temp_db, "node:A", "Node A", "concept")
        await knowledge_graph_service.upsert_entity(temp_db, "node:B", "Node B", "concept")
        await knowledge_graph_service.upsert_entity(temp_db, "node:C", "Node C", "concept")
        await knowledge_graph_service.upsert_entity(temp_db, "node:Isolated", "Isolated", "concept")

        await knowledge_graph_service.add_relation(temp_db, "node:A", "connects", "node:B")
        await knowledge_graph_service.add_relation(temp_db, "node:B", "connects", "node:C")

        neighborhood = await knowledge_graph_service.get_neighborhood(
            db=temp_db, entity_id="node:A", max_depth=2
        )
        node_ids = {n["id"] for n in neighborhood["nodes"]}
        assert "node:A" in node_ids
        assert "node:B" in node_ids
        assert "node:C" in node_ids
        assert "node:Isolated" not in node_ids
        assert len(neighborhood["edges"]) >= 2

    @pytest.mark.asyncio
    async def test_recursive_cte_shortest_path(self, temp_db: DatabaseManager):
        """Recursive CTE finds shortest path between connected entities."""
        await knowledge_graph_service.upsert_entity(temp_db, "p:start", "Start", "concept")
        await knowledge_graph_service.upsert_entity(temp_db, "p:mid", "Mid", "concept")
        await knowledge_graph_service.upsert_entity(temp_db, "p:end", "End", "concept")

        await knowledge_graph_service.add_relation(temp_db, "p:start", "leads_to", "p:mid")
        await knowledge_graph_service.add_relation(temp_db, "p:mid", "leads_to", "p:end")

        path = await knowledge_graph_service.find_path(temp_db, "p:start", "p:end", max_depth=3)
        assert len(path) == 3
        assert path[0]["node_id"] == "p:start"
        assert path[1]["node_id"] == "p:mid"
        assert path[2]["node_id"] == "p:end"

    @pytest.mark.asyncio
    async def test_auto_index_book_and_notes(self, temp_db: DatabaseManager, sample_hash_a: str):
        """index_book creates entities for author, category, keywords; index_notes captures wikilinks and hashtags."""
        book_data = {
            "dosya_hash": sample_hash_a,
            "kitap_adi": "Varlık ve Zaman",
            "yazar": "Martin Heidegger",
            "kategori": "Felsefe",
            "alt_kategori": "Ontoloji",
            "keywords": "Dasein, Fenomenoloji, Zaman",
        }
        res = await knowledge_graph_service.index_book(temp_db, book_data)
        assert res["entities"] >= 4
        assert res["relations"] >= 4

        # Add notes with wikilinks & hashtags
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_notlari (id, dosya_hash, sayfa_no, not_metni, secilen_metin)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "note-1",
                sample_hash_a,
                42,
                "Bu kavram [[Otantik Yaşam]] üzerine #felsefe",
                "Dasein kavramı",
            ),
        )
        await temp_db.conn.commit()

        note_res = await knowledge_graph_service.index_notes_for_book(temp_db, sample_hash_a)
        assert note_res["entities"] >= 2
        assert note_res["relations"] >= 2

        # Verify [[Otantik Yaşam]] concept exists
        concept = await knowledge_graph_service.get_entity(temp_db, "concept:otantik_yaşam")
        assert concept is not None
        assert concept["name"] == "Otantik Yaşam"


class TestSerendipityEngine:
    """Tests for cross-book discovery and note serendipity."""

    @pytest.mark.asyncio
    async def test_cross_book_discovery(
        self, temp_db: DatabaseManager, sample_hash_a: str, sample_hash_b: str
    ):
        """Serendipity engine matches passages in other books and user notes, excluding current book."""
        # 1. Insert two books
        await temp_db.conn.execute(
            """
            INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar, kategori, has_cover)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sample_hash_a, "kitap_a.pdf", "Yapay Zeka ve Gelecek", "Ali Yılmaz", "Teknoloji", 1),
        )
        await temp_db.conn.execute(
            """
            INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar, kategori, has_cover)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sample_hash_b, "kitap_b.pdf", "Bilinç ve Zihin Felsefesi", "Ayşe Kaya", "Felsefe", 1),
        )

        # 2. Index chunks in book B about consciousness
        chunks_b = [
            (
                sample_hash_b,
                15,
                0,
                "Yapay zeka sistemleri insan bilinci ve zihin modellerini taklit edebilir.",
                78,
                None,
            ),
            (
                sample_hash_b,
                16,
                1,
                "Bilişsel bilim yapay zeka ve sinirbilim kesişiminde gelişmektedir.",
                72,
                None,
            ),
        ]
        await temp_db.conn.executemany(
            """
            INSERT INTO kitap_chunks (dosya_hash, sayfa_no, chunk_index, metin, char_count, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            chunks_b,
        )
        await temp_db.conn.executemany(
            """
            INSERT INTO kitap_chunks_fts (dosya_hash, sayfa_no, chunk_index, metin)
            VALUES (?, ?, ?, ?)
            """,
            [(c[0], c[1], c[2], c[3]) for c in chunks_b],
        )

        # 3. Add note in book B
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_notlari (id, dosya_hash, sayfa_no, secilen_metin, not_metni)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("note-b1", sample_hash_b, 15, "Yapay zeka modelleri", "Çok önemli yapay zeka tespiti"),
        )
        await temp_db.conn.commit()

        # Run serendipity query while reading Book A
        result = await serendipity_engine.find_connections(
            db=temp_db,
            current_book_hash=sample_hash_a,
            query_text="yapay zeka bilinci",
            limit=5,
        )

        assert result["source_book_hash"] == sample_hash_a
        assert len(result["cross_book_passages"]) > 0
        # All cross book passages must belong to Book B, never Book A!
        for p in result["cross_book_passages"]:
            assert p["dosya_hash"] == sample_hash_b
            assert p["kitap_baslik"] == "Bilinç ve Zihin Felsefesi"

        assert len(result["related_notes"]) > 0
        assert result["related_notes"][0]["dosya_hash"] == sample_hash_b


class TestMultiAgentDebateEngine:
    """Tests for Dialectic Multi-Agent Debate and citation grounding."""

    def test_citation_extractor(self):
        """_extract_citations extracts page integers correctly."""
        text = "Bu sav [Sayfa 42] ve [Sayfa 105] kaynaklarına dayanır. Ayrıca [sayfa 42] tekrarlanmıştır."
        cites = _extract_citations(text)
        assert cites == [42, 105]

    @pytest.mark.asyncio
    async def test_deterministic_grounded_debate(
        self, temp_db: DatabaseManager, sample_hash_a: str, sample_hash_b: str
    ):
        """Debate engine runs multi-round dialectic synthesis grounded in real book chunks."""
        # Insert books
        await temp_db.conn.execute(
            """
            INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar, kategori)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sample_hash_a, "kitap_a.pdf", "Rasyonalizmin Zaferi", "Descartes", "Felsefe"),
        )
        await temp_db.conn.execute(
            """
            INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar, kategori)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sample_hash_b, "kitap_b.pdf", "Ampirizm ve Deneyim", "John Locke", "Felsefe"),
        )

        # Chunks for Book A
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_chunks (dosya_hash, sayfa_no, chunk_index, metin, char_count, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sample_hash_a,
                24,
                0,
                "Bilgi akıl yoluyla doğuştan gelir ve tümdengelimle inşa edilir.",
                60,
                None,
            ),
        )
        await temp_db.conn.execute(
            "INSERT INTO kitap_chunks_fts (dosya_hash, sayfa_no, chunk_index, metin) VALUES (?, ?, ?, ?)",
            (
                sample_hash_a,
                24,
                0,
                "Bilgi akıl yoluyla doğuştan gelir ve tümdengelimle inşa edilir.",
            ),
        )

        # Chunks for Book B
        await temp_db.conn.execute(
            """
            INSERT INTO kitap_chunks (dosya_hash, sayfa_no, chunk_index, metin, char_count, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sample_hash_b,
                55,
                0,
                "İnsan zihni boş bir levhadır (tabula rasa); bütün bilgi deneyimle edinilir.",
                72,
                None,
            ),
        )
        await temp_db.conn.execute(
            "INSERT INTO kitap_chunks_fts (dosya_hash, sayfa_no, chunk_index, metin) VALUES (?, ?, ?, ?)",
            (
                sample_hash_b,
                55,
                0,
                "İnsan zihni boş bir levhadır (tabula rasa); bütün bilgi deneyimle edinilir.",
            ),
        )
        await temp_db.conn.commit()

        # Run debate
        debate = await multi_agent_debate_engine.conduct_debate(
            db=temp_db,
            book_hashes=[sample_hash_a, sample_hash_b],
            topic="Bilginin Kaynağı: Akıl mı Deneyim mi?",
            rounds=2,
        )

        assert debate["topic"] == "Bilginin Kaynağı: Akıl mı Deneyim mi?"
        assert len(debate["books"]) == 2
        assert debate["books"][0]["title"] == "Rasyonalizmin Zaferi"
        assert debate["books"][1]["title"] == "Ampirizm ve Deneyim"

        assert len(debate["rounds"]) == 2
        r1 = debate["rounds"][0]
        assert r1["round"] == 1
        assert "Sayfa" in r1["agent_a"]["response"]
        assert "Sayfa" in r1["agent_b"]["response"]

        # Synthesis
        synth = debate["synthesis"]
        assert len(synth["agreements"]) >= 1
        assert len(synth["contradictions"]) >= 1
        assert len(synth["unifying_principle"]) > 10
        assert len(debate["citations"]) >= 2


class TestDebateAndGraphAPIEndpoints:
    """End-to-end integration tests for HTTP API endpoints."""

    @pytest.mark.asyncio
    async def test_api_debate_endpoint(
        self,
        async_client: httpx.AsyncClient,
        temp_db: DatabaseManager,
        sample_hash_a: str,
        sample_hash_b: str,
    ):
        """POST /api/debate returns dialectic debate payload."""
        # Insert test books
        await temp_db.conn.execute(
            "INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar) VALUES (?, ?, ?, ?)",
            (sample_hash_a, "a.pdf", "Devlet", "Platon"),
        )
        await temp_db.conn.execute(
            "INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar) VALUES (?, ?, ?, ?)",
            (sample_hash_b, "b.pdf", "Politika", "Aristoteles"),
        )
        await temp_db.conn.commit()

        payload = {
            "book_hashes": [sample_hash_a, sample_hash_b],
            "topic": "İdeal Toplum ve Adalet",
            "rounds": 1,
        }
        res = await async_client.post("/api/debate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["topic"] == "İdeal Toplum ve Adalet"
        assert len(data["rounds"]) == 1
        assert "synthesis" in data

    @pytest.mark.asyncio
    async def test_api_serendipity_endpoint(
        self, async_client: httpx.AsyncClient, temp_db: DatabaseManager, sample_hash_a: str
    ):
        """GET /api/books/{hash}/serendipity returns discovery response."""
        await temp_db.conn.execute(
            "INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi) VALUES (?, ?, ?)",
            (sample_hash_a, "a.pdf", "Kaynak Kitap"),
        )
        await temp_db.conn.commit()

        res = await async_client.get(f"/api/books/{sample_hash_a}/serendipity?text=bilim")
        assert res.status_code == 200
        data = res.json()
        assert data["source_book_hash"] == sample_hash_a
        assert "cross_book_passages" in data

    @pytest.mark.asyncio
    async def test_api_graph_endpoints_lifecycle(
        self, async_client: httpx.AsyncClient, temp_db: DatabaseManager, sample_hash_a: str
    ):
        """Full lifecycle of /api/graph endpoints: stats, index-book, neighbors, and shortest path."""
        # Insert book
        await temp_db.conn.execute(
            "INSERT INTO kitaplar (dosya_hash, dosya_adi, kitap_adi, yazar, kategori) VALUES (?, ?, ?, ?, ?)",
            (sample_hash_a, "test.pdf", "Kozmos", "Carl Sagan", "Astronomi"),
        )
        await temp_db.conn.commit()

        # 1. Index book to graph
        index_res = await async_client.post(f"/api/graph/index-book/{sample_hash_a}")
        assert index_res.status_code == 200
        assert index_res.json()["success"] is True

        # 2. Get stats
        stats_res = await async_client.get("/api/graph/stats")
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_entities"] >= 3

        # 3. Get neighbors
        book_entity_id = f"book:{sample_hash_a}"
        neigh_res = await async_client.get(f"/api/graph/neighbors/{book_entity_id}")
        assert neigh_res.status_code == 200
        neigh = neigh_res.json()
        assert len(neigh["nodes"]) >= 2
        assert len(neigh["edges"]) >= 2

        # 4. Search entities
        search_res = await async_client.get("/api/graph/search?q=Sagan")
        assert search_res.status_code == 200
        assert search_res.json()["count"] >= 1
