"""Knowledge Graph service using in-process SQLite Recursive CTE triplestore."""

import json
import logging
import re
from typing import Any

from app.database import DatabaseManager
from app.logger import log_event

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Zero-Bloat Triplestore and Graph Traversal Engine powered by SQLite Recursive CTEs."""

    @staticmethod
    async def upsert_entity(
        db: DatabaseManager,
        entity_id: str,
        name: str,
        entity_type: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert or update an entity node in kg_entities."""
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        sql = """
            INSERT INTO kg_entities (id, name, entity_type, description, metadata)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                entity_type = excluded.entity_type,
                description = excluded.description,
                metadata = excluded.metadata
        """
        await db.conn.execute(sql, (entity_id, name, entity_type, description, meta_json))
        await db.conn.commit()
        return {
            "id": entity_id,
            "name": name,
            "entity_type": entity_type,
            "description": description,
            "metadata": metadata or {},
        }

    @staticmethod
    async def get_entity(db: DatabaseManager, entity_id: str) -> dict[str, Any] | None:
        """Fetch a single entity node by its primary key ID."""
        cursor = await db.conn.execute(
            "SELECT id, name, entity_type, description, metadata, created_at FROM kg_entities WHERE id = ?",
            (entity_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        meta = {}
        try:
            meta = json.loads(row[4] or "{}")
        except json.JSONDecodeError as err:
            logger.debug("Failed parsing entity metadata for %s: %s", entity_id, err)
        return {
            "id": row[0],
            "name": row[1],
            "entity_type": row[2],
            "description": row[3],
            "metadata": meta,
            "created_at": str(row[5]),
        }

    @staticmethod
    async def search_entities(
        db: DatabaseManager,
        query: str = "",
        entity_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search entities by name substring and optional entity_type filter."""
        sql = "SELECT id, name, entity_type, description, metadata FROM kg_entities WHERE 1=1"
        params: list[Any] = []
        if query and query.strip():
            sql += " AND (name LIKE ? OR description LIKE ?)"
            clean_q = f"%{query.strip()}%"
            params.extend([clean_q, clean_q])
        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)
        sql += " ORDER BY name ASC LIMIT ?"
        params.append(limit)

        cursor = await db.conn.execute(sql, params)
        rows = await cursor.fetchall()
        results: list[dict[str, Any]] = []
        for r in rows:
            meta = {}
            try:
                meta = json.loads(r[4] or "{}")
            except json.JSONDecodeError as err:
                logger.debug("Entity metadata decode error: %s", err)
            results.append(
                {
                    "id": r[0],
                    "name": r[1],
                    "entity_type": r[2],
                    "description": r[3],
                    "metadata": meta,
                }
            )
        return results

    @staticmethod
    async def add_relation(
        db: DatabaseManager,
        source_id: str,
        relation_type: str,
        target_id: str,
        weight: float = 1.0,
        source_evidence: str = "",
    ) -> int:
        """Create a directed relation between source and target entities."""
        # Ensure endpoints exist
        src = await KnowledgeGraphService.get_entity(db, source_id)
        if not src:
            await KnowledgeGraphService.upsert_entity(
                db, entity_id=source_id, name=source_id, entity_type="concept"
            )
        tgt = await KnowledgeGraphService.get_entity(db, target_id)
        if not tgt:
            await KnowledgeGraphService.upsert_entity(
                db, entity_id=target_id, name=target_id, entity_type="concept"
            )

        cursor = await db.conn.execute(
            """
            INSERT INTO kg_relations (source_id, relation_type, target_id, weight, source_evidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_id, relation_type, target_id, weight, source_evidence),
        )
        await db.conn.commit()
        return int(cursor.lastrowid or 0)

    @staticmethod
    async def get_relations(
        db: DatabaseManager,
        entity_id: str | None = None,
        relation_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch relations matching criteria."""
        sql = "SELECT id, source_id, relation_type, target_id, weight, source_evidence FROM kg_relations WHERE 1=1"
        params: list[Any] = []
        if entity_id:
            sql += " AND (source_id = ? OR target_id = ?)"
            params.extend([entity_id, entity_id])
        if relation_type:
            sql += " AND relation_type = ?"
            params.append(relation_type)
        sql += " LIMIT ?"
        params.append(limit)

        cursor = await db.conn.execute(sql, params)
        rows = await cursor.fetchall()
        results: list[dict[str, Any]] = []
        for r in rows:
            results.append(
                {
                    "id": r[0],
                    "source_id": r[1],
                    "relation_type": r[2],
                    "target_id": r[3],
                    "weight": r[4],
                    "source_evidence": r[5],
                }
            )
        return results

    @staticmethod
    async def get_neighborhood(
        db: DatabaseManager,
        entity_id: str,
        max_depth: int = 2,
        limit: int = 50,
    ) -> dict[str, list[dict[str, Any]]]:
        """Traverse the knowledge graph using a SQLite Recursive CTE to find all neighbors up to max_depth."""
        if not entity_id:
            return {"nodes": [], "edges": []}

        # Recursive CTE exploring neighbors
        cte_sql = """
            WITH RECURSIVE neighborhood(node_id, depth, visited_path) AS (
                SELECT ?, 0, ?
                UNION
                SELECT
                    CASE WHEN r.source_id = n.node_id THEN r.target_id ELSE r.source_id END,
                    n.depth + 1,
                    n.visited_path || ',' || CASE WHEN r.source_id = n.node_id THEN r.target_id ELSE r.source_id END
                FROM neighborhood n
                JOIN kg_relations r ON (r.source_id = n.node_id OR r.target_id = n.node_id)
                WHERE n.depth < ?
                  AND instr(n.visited_path, ',' || CASE WHEN r.source_id = n.node_id THEN r.target_id ELSE r.source_id END) = 0
            )
            SELECT DISTINCT node_id, min(depth) as min_depth
            FROM neighborhood
            GROUP BY node_id
            ORDER BY min_depth ASC
            LIMIT ?
        """
        init_path = f",{entity_id}"
        cursor = await db.conn.execute(cte_sql, (entity_id, init_path, max_depth, limit))
        discovered_rows = await cursor.fetchall()
        if not discovered_rows:
            return {"nodes": [], "edges": []}

        node_ids = [r[0] for r in discovered_rows]
        depth_map = {r[0]: r[1] for r in discovered_rows}

        # Fetch node details
        placeholders = ",".join("?" for _ in node_ids)
        node_cursor = await db.conn.execute(
            f"SELECT id, name, entity_type, description, metadata FROM kg_entities WHERE id IN ({placeholders})",
            node_ids,
        )
        nodes: list[dict[str, Any]] = []
        for nr in await node_cursor.fetchall():
            meta = {}
            try:
                meta = json.loads(nr[4] or "{}")
            except json.JSONDecodeError as err:
                logger.debug("Node metadata decode error: %s", err)
            nodes.append(
                {
                    "id": nr[0],
                    "name": nr[1],
                    "entity_type": nr[2],
                    "description": nr[3],
                    "metadata": meta,
                    "depth": depth_map.get(nr[0], 0),
                }
            )

        # Fetch connecting edges between these nodes
        edge_cursor = await db.conn.execute(
            f"""
            SELECT id, source_id, relation_type, target_id, weight, source_evidence
            FROM kg_relations
            WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})
            """,
            node_ids + node_ids,
        )
        edges: list[dict[str, Any]] = []
        for er in await edge_cursor.fetchall():
            edges.append(
                {
                    "id": er[0],
                    "from": er[1],
                    "source_id": er[1],
                    "relation_type": er[2],
                    "to": er[3],
                    "target_id": er[3],
                    "weight": er[4],
                    "source_evidence": er[5],
                }
            )

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    async def find_path(
        db: DatabaseManager,
        source_id: str,
        target_id: str,
        max_depth: int = 4,
    ) -> list[dict[str, Any]]:
        """Find the shortest relationship path between two entities using Recursive CTE."""
        if source_id == target_id:
            return [{"node_id": source_id, "depth": 0}]

        cte_sql = """
            WITH RECURSIVE path_search(current_id, depth, path_str, relations_str) AS (
                SELECT ?, 0, ?, ''
                UNION ALL
                SELECT
                    CASE WHEN r.source_id = p.current_id THEN r.target_id ELSE r.source_id END,
                    p.depth + 1,
                    p.path_str || '->' || CASE WHEN r.source_id = p.current_id THEN r.target_id ELSE r.source_id END,
                    CASE WHEN p.relations_str = '' THEN r.relation_type ELSE p.relations_str || '->' || r.relation_type END
                FROM path_search p
                JOIN kg_relations r ON (r.source_id = p.current_id OR r.target_id = p.current_id)
                WHERE p.depth < ?
                  AND instr(p.path_str, CASE WHEN r.source_id = p.current_id THEN r.target_id ELSE r.source_id END) = 0
            )
            SELECT depth, path_str, relations_str
            FROM path_search
            WHERE current_id = ?
            ORDER BY depth ASC
            LIMIT 1
        """
        cursor = await db.conn.execute(cte_sql, (source_id, source_id, max_depth, target_id))
        row = await cursor.fetchone()
        if not row:
            return []

        _depth, path_str, relations_str = row
        nodes = path_str.split("->")
        relations = relations_str.split("->") if relations_str else []

        path_details: list[dict[str, Any]] = []
        for idx, node in enumerate(nodes):
            rel = relations[idx - 1] if idx > 0 and idx - 1 < len(relations) else None
            path_details.append(
                {
                    "node_id": node,
                    "depth": idx,
                    "via_relation": rel,
                }
            )
        return path_details

    @classmethod
    async def index_book(cls, db: DatabaseManager, book: dict[str, Any]) -> dict[str, int]:
        """Automatically extract and index book metadata into the knowledge graph."""
        file_hash = book.get("dosya_hash")
        if not file_hash:
            return {"entities": 0, "relations": 0}

        title = (
            book.get("kitap_adi") or book.get("baslik") or book.get("dosya_adi") or file_hash[:8]
        )
        author = (book.get("yazar") or "").strip()
        category = (book.get("kategori") or "").strip()
        subcat = (book.get("alt_kategori") or "").strip()
        keywords = book.get("anahtar_kelimeler") or book.get("keywords") or ""

        entities_count = 0
        relations_count = 0

        # 1. Book node
        book_entity_id = f"book:{file_hash}"
        await cls.upsert_entity(
            db,
            entity_id=book_entity_id,
            name=title,
            entity_type="book",
            description=f"Sayfa: {book.get('sayfa_sayisi', 0)} | Boyut: {book.get('dosya_boyutu', 0)}",
            metadata={"dosya_hash": file_hash, "dosya_adi": book.get("dosya_adi", "")},
        )
        entities_count += 1

        # 2. Author node & relation
        if author and author.lower() not in ("bilinmiyor", "unknown", "yok", ""):
            author_id = f"author:{author.lower().replace(' ', '_')}"
            await cls.upsert_entity(
                db,
                entity_id=author_id,
                name=author,
                entity_type="author",
                description="Yazar",
            )
            entities_count += 1
            await cls.add_relation(
                db,
                source_id=book_entity_id,
                relation_type="authored_by",
                target_id=author_id,
                weight=1.0,
            )
            relations_count += 1

        # 3. Category & Subcategory nodes
        if category:
            cat_id = f"category:{category.lower().replace(' ', '_')}"
            await cls.upsert_entity(
                db,
                entity_id=cat_id,
                name=category,
                entity_type="category",
                description="Ana Kategori",
            )
            entities_count += 1
            await cls.add_relation(
                db,
                source_id=book_entity_id,
                relation_type="belongs_to",
                target_id=cat_id,
                weight=0.9,
            )
            relations_count += 1

            if subcat:
                subcat_id = f"category:{subcat.lower().replace(' ', '_')}"
                await cls.upsert_entity(
                    db,
                    entity_id=subcat_id,
                    name=subcat,
                    entity_type="category",
                    description=f"{category} Alt Kategorisi",
                )
                entities_count += 1
                await cls.add_relation(
                    db,
                    source_id=book_entity_id,
                    relation_type="belongs_to",
                    target_id=subcat_id,
                    weight=0.8,
                )
                await cls.add_relation(
                    db,
                    source_id=subcat_id,
                    relation_type="subclass_of",
                    target_id=cat_id,
                    weight=1.0,
                )
                relations_count += 2

        # 4. Keywords / Concepts
        if keywords:
            tags = [t.strip() for t in re.split(r"[,;\n]", str(keywords)) if t.strip()]
            for tag in tags[:10]:
                tag_id = f"concept:{tag.lower().replace(' ', '_')}"
                await cls.upsert_entity(
                    db,
                    entity_id=tag_id,
                    name=tag,
                    entity_type="concept",
                    description="Kavram / Konu Başlığı",
                )
                entities_count += 1
                await cls.add_relation(
                    db,
                    source_id=book_entity_id,
                    relation_type="discusses",
                    target_id=tag_id,
                    weight=0.7,
                )
                relations_count += 1

        log_event(
            "ai",
            "INFO",
            f"Knowledge Graph indekslendi: {title} ({entities_count} varlık, {relations_count} ilişki)",
        )
        return {"entities": entities_count, "relations": relations_count}

    @classmethod
    async def index_notes_for_book(cls, db: DatabaseManager, file_hash: str) -> dict[str, int]:
        """Extract [[Wikilinks]] and #tags from book notes and link them in the graph."""
        book_id = f"book:{file_hash}"
        cursor = await db.conn.execute(
            "SELECT id, sayfa_no, not_metni, secilen_metin FROM kitap_notlari WHERE dosya_hash = ?",
            (file_hash,),
        )
        notes = await cursor.fetchall()
        entities = 0
        relations = 0

        for row in notes:
            _note_id, sayfa_no, not_text, sel_text = row
            full_text = f"{not_text or ''} {sel_text or ''}"

            # 1. Wikilinks [[Concept Name]]
            wikilinks = re.findall(r"\[\[(.*?)\]\]", full_text)
            for wl in wikilinks:
                clean_concept = wl.strip()
                if not clean_concept:
                    continue
                cid = f"concept:{clean_concept.lower().replace(' ', '_')}"
                await cls.upsert_entity(
                    db,
                    entity_id=cid,
                    name=clean_concept,
                    entity_type="concept",
                    description=f"Wikilink notu (Sayfa {sayfa_no})",
                )
                entities += 1
                await cls.add_relation(
                    db,
                    source_id=book_id,
                    relation_type="references",
                    target_id=cid,
                    weight=0.8,
                    source_evidence=f"Sayfa {sayfa_no}: {not_text or sel_text or ''}",
                )
                relations += 1

            # 2. Hashtags #Topic
            hashtags = re.findall(r"#([\w-]+)", full_text)
            for ht in hashtags:
                clean_tag = ht.strip()
                if not clean_tag or clean_tag.isdigit():
                    continue
                tid = f"concept:{clean_tag.lower()}"
                await cls.upsert_entity(
                    db,
                    entity_id=tid,
                    name=f"#{clean_tag}",
                    entity_type="concept",
                    description=f"Etiket notu (Sayfa {sayfa_no})",
                )
                entities += 1
                await cls.add_relation(
                    db,
                    source_id=book_id,
                    relation_type="discusses",
                    target_id=tid,
                    weight=0.7,
                    source_evidence=f"Sayfa {sayfa_no}",
                )
                relations += 1

        return {"entities": entities, "relations": relations}

    @staticmethod
    async def get_graph_stats(db: DatabaseManager) -> dict[str, Any]:
        """Return total entity and relation count breakdowns."""
        c1 = await db.conn.execute("SELECT count(*) FROM kg_entities")
        r1 = await c1.fetchone()
        total_entities = int(r1[0]) if r1 else 0

        c2 = await db.conn.execute("SELECT count(*) FROM kg_relations")
        r2 = await c2.fetchone()
        total_relations = int(r2[0]) if r2 else 0

        c3 = await db.conn.execute(
            "SELECT entity_type, count(*) FROM kg_entities GROUP BY entity_type"
        )
        entity_types = {row[0]: row[1] for row in await c3.fetchall()}

        c4 = await db.conn.execute(
            "SELECT relation_type, count(*) FROM kg_relations GROUP BY relation_type"
        )
        relation_types = {row[0]: row[1] for row in await c4.fetchall()}

        return {
            "total_entities": total_entities,
            "total_relations": total_relations,
            "entity_types": entity_types,
            "relation_types": relation_types,
        }


# Global singleton instance
knowledge_graph_service = KnowledgeGraphService()
