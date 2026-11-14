"""Document Repository implementing clean, pure database CRUD operations."""

import sqlite3
from typing import Any

import aiosqlite

ALLOWED_UPDATE_COLUMNS: frozenset[str] = frozenset(
    {
        "kitap_adi",
        "yazar",
        "kategori",
        "alt_kategori",
        "ozet",
        "anahtar_kelimeler",
        "dosya_yolu",
    }
)


class DocumentRepository:
    """Repository handling pure SQLite database operations for documents and collections.

    Contains NO business logic, filesystem operations, or external service integrations.
    """

    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn
        if getattr(self.conn, "row_factory", None) is None:
            self.conn.row_factory = aiosqlite.Row

    async def add_book(self, data: dict) -> None:
        """Add or update a book in the database."""
        query = """
            INSERT INTO kitaplar
            (kitap_adi, yazar, kategori, alt_kategori, ozet, anahtar_kelimeler, dosya_adi, dosya_hash, dosya_yolu, has_cover)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dosya_hash) DO UPDATE SET
                kitap_adi=excluded.kitap_adi,
                yazar=excluded.yazar,
                kategori=excluded.kategori,
                alt_kategori=excluded.alt_kategori,
                ozet=excluded.ozet,
                anahtar_kelimeler=excluded.anahtar_kelimeler,
                dosya_adi=excluded.dosya_adi,
                dosya_yolu=excluded.dosya_yolu,
                has_cover=excluded.has_cover
        """

        def safe_str(val: object) -> str:
            if val is None:
                return ""
            if isinstance(val, list):
                return ", ".join(map(str, val))
            return str(val)

        params = (
            safe_str(data.get("kitap_adi")),
            safe_str(data.get("yazar")),
            safe_str(data.get("kategori")),
            safe_str(data.get("alt_kategori")),
            safe_str(data.get("ozet")),
            safe_str(data.get("anahtar_kelimeler")),
            safe_str(data.get("dosya_adi")),
            safe_str(data.get("dosya_hash")),
            safe_str(data.get("dosya_yolu")),
            1 if data.get("has_cover") else 0,
        )
        await self.conn.execute(query, params)
        await self.conn.commit()

    async def _build_collection_filter(self, collection_id: int) -> tuple[list[str], list[Any]]:
        """Compile collection filter clauses and parameters for static or dynamic smart collections."""
        cur_col = await self.conn.execute(
            "SELECT is_dynamic, rule_json FROM koleksiyonlar WHERE id = ?",
            (collection_id,),
        )
        col_row = await cur_col.fetchone()
        if col_row and col_row["is_dynamic"] and col_row["rule_json"]:
            import json

            try:
                rule_data = json.loads(col_row["rule_json"])
                from app.services.smart_collections import smart_collection_compiler

                return smart_collection_compiler.compile_rules(rule_data)
            except Exception as e:
                from app.logger import log_event

                log_event(
                    "database",
                    "WARNING",
                    f"Dinamik koleksiyon kuralı derleme hatası: {e}",
                )
                return ["1=0"], []

        return [
            "dosya_hash IN (SELECT kitap_hash FROM koleksiyon_kitap WHERE koleksiyon_id = ?)"
        ], [collection_id]

    async def _populate_book_collections(self, books: list[dict]) -> None:
        """Enrich books list with collection ID associations in a single query."""
        if not books:
            return
        hashes = [b["dosya_hash"] for b in books]
        placeholders = ",".join("?" * len(hashes))
        cur = await self.conn.execute(
            f"SELECT koleksiyon_id, kitap_hash FROM koleksiyon_kitap WHERE kitap_hash IN ({placeholders})",
            hashes,
        )
        book_col_map: dict[str, list[int]] = {}
        for col_id, b_hash in await cur.fetchall():
            book_col_map.setdefault(b_hash, []).append(col_id)

        for b in books:
            b["koleksiyonlar"] = book_col_map.get(b["dosya_hash"], [])

    async def get_all_books(
        self,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
        search: str | None = None,
        favorite: bool | None = None,
        collection_id: int | None = None,
        sort: str | None = None,
    ) -> dict:
        """Get books with pagination and optional category, search, favorite, collection, and sort filters."""
        cols = [
            "id",
            "kitap_adi",
            "yazar",
            "kategori",
            "alt_kategori",
            "ozet",
            "anahtar_kelimeler",
            "dosya_adi",
            "dosya_hash",
            "is_favorite",
            "okunulan_sayfa",
            "ekleme_tarihi",
            "sira_numarasi",
            "has_cover",
        ]
        count_query = "SELECT COUNT(*) FROM kitaplar"
        select_query = f"SELECT {', '.join(cols)} FROM kitaplar"

        filters = []
        params = []
        if category and category != "all":
            filters.append("kategori = ?")
            params.append(category)

        if favorite is not None:
            filters.append("is_favorite = ?")
            params.append(1 if favorite else 0)

        if collection_id is not None:
            col_clauses, col_params = await self._build_collection_filter(collection_id)
            filters.extend(col_clauses)
            params.extend(col_params)

        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                "(kitap_adi LIKE ? OR yazar LIKE ? OR anahtar_kelimeler LIKE ? OR ozet LIKE ? OR kategori LIKE ?)"
            )
            params.extend([term, term, term, term, term])

        if filters:
            where_clause = " WHERE " + " AND ".join(filters)
            count_query += where_clause
            select_query += where_clause

        allowed_sorts = {
            "sira_asc": "sira_numarasi ASC, ekleme_tarihi DESC",
            "date_desc": "ekleme_tarihi DESC",
            "date_asc": "ekleme_tarihi ASC",
            "title_asc": "kitap_adi COLLATE NOCASE ASC",
            "title_desc": "kitap_adi COLLATE NOCASE DESC",
            "author_asc": "yazar COLLATE NOCASE ASC",
            "author_desc": "yazar COLLATE NOCASE DESC",
            "pages_desc": "okunulan_sayfa DESC",
        }
        order_clause = allowed_sorts.get(sort, "sira_numarasi ASC, ekleme_tarihi DESC")
        select_query += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"

        cursor = await self.conn.execute(count_query, params)
        count_row = await cursor.fetchone()
        total_count = int(count_row[0]) if count_row else 0

        cursor = await self.conn.execute(select_query, [*params, limit, offset])

        books = []
        for row in await cursor.fetchall():
            if hasattr(row, "keys"):
                d = dict(row)
            else:
                d = dict(zip(cols, row, strict=False))
            d["has_cover"] = bool(d.get("has_cover", 0))
            d["is_favorite"] = bool(d.get("is_favorite", 0))
            books.append(d)

        await self._populate_book_collections(books)

        return {"total": total_count, "items": books, "limit": limit, "offset": offset}

    async def get_collections(self) -> list[dict]:
        """Get all collections."""
        cur = await self.conn.execute(
            "SELECT id, isim, is_dynamic, rule_json FROM koleksiyonlar ORDER BY isim"
        )
        return [dict(row) for row in await cur.fetchall()]

    async def add_collection(
        self, name: str, is_dynamic: bool = False, rule_json: str | None = None
    ) -> dict | None:
        """Add a new collection (static or dynamic)."""
        try:
            cur = await self.conn.execute(
                "INSERT INTO koleksiyonlar (isim, is_dynamic, rule_json) VALUES (?, ?, ?)",
                (name, 1 if is_dynamic else 0, rule_json),
            )
            await self.conn.commit()
            return {
                "id": cur.lastrowid,
                "isim": name,
                "is_dynamic": 1 if is_dynamic else 0,
                "rule_json": rule_json,
            }
        except sqlite3.IntegrityError:
            return None

    async def add_book_to_col(self, col_id: int, b_hash: str) -> None:
        """Add a book to a collection."""
        await self.conn.execute(
            "INSERT OR IGNORE INTO koleksiyon_kitap (koleksiyon_id, kitap_hash) VALUES (?, ?)",
            (col_id, b_hash),
        )
        await self.conn.commit()

    async def rm_book_from_col(self, col_id: int, b_hash: str) -> None:
        """Remove a book from a collection."""
        await self.conn.execute(
            "DELETE FROM koleksiyon_kitap WHERE koleksiyon_id = ? AND kitap_hash = ?",
            (col_id, b_hash),
        )
        await self.conn.commit()

    async def delete_collection(self, col_id: int) -> None:
        """Delete a collection and its book associations (cascaded via foreign keys)."""
        await self.conn.execute("DELETE FROM koleksiyonlar WHERE id = ?", (col_id,))
        await self.conn.commit()

    async def get_collection_books(self, col_id: int) -> list[dict]:
        """Get all books within a collection."""
        try:
            target_id = int(col_id)
        except (TypeError, ValueError):
            target_id = col_id

        hashes_cur = await self.conn.execute(
            "SELECT kitap_hash FROM koleksiyon_kitap WHERE koleksiyon_id = ?",
            (target_id,),
        )
        hashes = [r[0] for r in await hashes_cur.fetchall()]

        if not hashes:
            return []

        placeholders = ",".join("?" * len(hashes))
        query = f"SELECT kitap_adi, yazar, dosya_hash, kategori FROM kitaplar WHERE dosya_hash IN ({placeholders})"
        cur = await self.conn.execute(query, hashes)
        return [dict(row) for row in await cur.fetchall()]

    async def update_reading_progress(self, file_hash: str, page: int) -> None:
        """Update reading progress for a book."""
        await self.conn.execute(
            "UPDATE kitaplar SET okunulan_sayfa = ? WHERE dosya_hash = ?",
            (page, file_hash),
        )
        await self.conn.commit()

    async def book_exists(self, file_hash: str) -> bool:
        """Check if a book exists by its hash."""
        cursor = await self.conn.execute(
            "SELECT 1 FROM kitaplar WHERE dosya_hash = ? LIMIT 1", (file_hash,)
        )
        return (await cursor.fetchone()) is not None

    async def toggle_favorite(self, file_hash: str) -> bool:
        """Toggle favorite status of a book."""
        cursor = await self.conn.execute(
            "SELECT is_favorite FROM kitaplar WHERE dosya_hash = ?", (file_hash,)
        )
        row = await cursor.fetchone()
        if row:
            new_status = 1 if not row[0] else 0
            await self.conn.execute(
                "UPDATE kitaplar SET is_favorite = ? WHERE dosya_hash = ?",
                (new_status, file_hash),
            )
            await self.conn.commit()
            return bool(new_status)
        return False

    async def delete_book(self, file_hash: str) -> None:
        """Delete a book and explicitly clean up all related child entities and search indices."""
        book_entity_id = f"book:{file_hash}"
        await self.conn.execute("DELETE FROM kitap_toc WHERE dosya_hash = ?", (file_hash,))
        await self.conn.execute("DELETE FROM kitap_notlari WHERE dosya_hash = ?", (file_hash,))
        await self.conn.execute("DELETE FROM koleksiyon_kitap WHERE kitap_hash = ?", (file_hash,))
        await self.conn.execute("DELETE FROM kitap_chunks WHERE dosya_hash = ?", (file_hash,))
        await self.conn.execute("DELETE FROM kitap_chunks_fts WHERE dosya_hash = ?", (file_hash,))
        await self.conn.execute(
            "DELETE FROM kg_relations WHERE source_id = ? OR target_id = ?",
            (book_entity_id, book_entity_id),
        )
        await self.conn.execute("DELETE FROM kg_entities WHERE id = ?", (book_entity_id,))
        await self.conn.execute("DELETE FROM kitaplar WHERE dosya_hash = ?", (file_hash,))
        await self.conn.commit()

    async def get_book_annotations(self, file_hash: str) -> list[dict]:
        """Get all annotations and highlights for a given book."""
        cur = await self.conn.execute(
            """
            SELECT id, dosya_hash, sayfa_no, secilen_metin, not_metni,
                   renk_hex, renk_sinif, koordinatlar, olusturma_tarihi, guncelleme_tarihi
            FROM kitap_notlari
            WHERE dosya_hash = ?
            ORDER BY sayfa_no ASC, olusturma_tarihi ASC
            """,
            (file_hash,),
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]

    async def save_book_annotation(self, ann: dict) -> dict:
        """Save or update an annotation for a book."""
        await self.conn.execute(
            """
            INSERT INTO kitap_notlari (
                id, dosya_hash, sayfa_no, secilen_metin, not_metni,
                renk_hex, renk_sinif, koordinatlar, guncelleme_tarihi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                sayfa_no = excluded.sayfa_no,
                secilen_metin = excluded.secilen_metin,
                not_metni = excluded.not_metni,
                renk_hex = excluded.renk_hex,
                renk_sinif = excluded.renk_sinif,
                koordinatlar = excluded.koordinatlar,
                guncelleme_tarihi = CURRENT_TIMESTAMP
            """,
            (
                ann["id"],
                ann["dosya_hash"],
                ann["sayfa_no"],
                ann.get("secilen_metin", ""),
                ann.get("not_metni", ""),
                ann.get("renk_hex", "#fef08a"),
                ann.get("renk_sinif", "yellow"),
                ann.get("koordinatlar", "[]"),
            ),
        )
        await self.conn.commit()
        return ann

    async def delete_book_annotation(self, annotation_id: str, file_hash: str) -> bool:
        """Delete an annotation by ID and book file hash."""
        cur = await self.conn.execute(
            "DELETE FROM kitap_notlari WHERE id = ? AND dosya_hash = ?",
            (annotation_id, file_hash),
        )
        await self.conn.commit()
        return cur.rowcount > 0

    async def get_book_notes_for_ai(self, file_hash: str) -> str:
        """Format user highlights and notes for LLM prompt context injection."""
        annotations = await self.get_book_annotations(file_hash)
        if not annotations:
            return ""

        formatted_items = []
        for a in annotations:
            parts = [f"[Sayfa {a.get('sayfa_no', 1)}]"]
            sel = (a.get("secilen_metin") or "").strip()
            note = (a.get("not_metni") or "").strip()
            if sel:
                # Truncate very long highlight text to avoid prompt bloat
                if len(sel) > 300:
                    sel = sel[:300] + "..."
                parts.append(f'Alıntı: "{sel}"')
            if note:
                parts.append(f'Kullanıcı Notu: "{note}"')
            formatted_items.append(" | ".join(parts))

        joined = "\n".join(formatted_items)
        return (
            "--- KULLANICININ BU KİTAPTAN ALDIĞI ÖZEL NOTLAR VE VURGULAR ---\n"
            f"{joined}\n"
            "----------------------------------------------------------------\n"
            "Kullanıcı bu kitaptan aldığı notlar, alıntılar veya işaretlemeler hakkında bir soru sorarsa veya özet isterse yukarıdaki verileri esas alarak yanıtla.\n\n"
        )

    async def update_book(self, file_hash: str, data: dict) -> None:
        """Update book metadata in the database."""
        updates = []
        params = []

        for key in ALLOWED_UPDATE_COLUMNS:
            if key in data and data[key] is not None:
                val = data[key]
                if isinstance(val, list):
                    val = ", ".join(map(str, val))
                updates.append(f"{key} = ?")
                params.append(val)

        if not updates:
            return

        query = f"UPDATE kitaplar SET {', '.join(updates)} WHERE dosya_hash = ?"
        params.append(file_hash)

        await self.conn.execute(query, params)
        await self.conn.commit()

    async def save_book_order(self, hash_list: list[str]) -> None:
        """Save custom book display order in a single batch operation."""
        if hash_list:
            await self.conn.executemany(
                "UPDATE kitaplar SET sira_numarasi = ? WHERE dosya_hash = ?",
                [(idx, file_hash) for idx, file_hash in enumerate(hash_list)],
            )
            await self.conn.commit()

    async def save_book_annotations_batch(self, annotations: list[dict]) -> int:
        """Batch insert or update annotations using executemany with single commit."""
        if not annotations:
            return 0
        query = """
            INSERT INTO kitap_notlari (
                id, dosya_hash, sayfa_no, secilen_metin, not_metni,
                renk_hex, renk_sinif, koordinatlar, guncelleme_tarihi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                sayfa_no = excluded.sayfa_no,
                secilen_metin = excluded.secilen_metin,
                not_metni = excluded.not_metni,
                renk_hex = excluded.renk_hex,
                renk_sinif = excluded.renk_sinif,
                koordinatlar = excluded.koordinatlar,
                guncelleme_tarihi = CURRENT_TIMESTAMP
        """
        params = [
            (
                a["id"],
                a["dosya_hash"],
                a["sayfa_no"],
                a.get("secilen_metin", ""),
                a.get("not_metni", ""),
                a.get("renk_hex", "#fef08a"),
                a.get("renk_sinif", "yellow"),
                a.get("koordinatlar", "[]"),
            )
            for a in annotations
        ]
        await self.conn.executemany(query, params)
        await self.conn.commit()
        return len(annotations)

    async def get_book_path(self, file_hash: str) -> tuple[str, str] | None:
        """Get file path and name for a book by its hash."""
        cursor = await self.conn.execute(
            "SELECT dosya_yolu, dosya_adi FROM kitaplar WHERE dosya_hash = ?",
            (file_hash,),
        )
        return await cursor.fetchone()

    async def get_book_by_hash(self, file_hash: str) -> dict | None:
        """Get complete book metadata record by its file hash."""
        cursor = await self.conn.execute(
            "SELECT * FROM kitaplar WHERE dosya_hash = ? LIMIT 1", (file_hash,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return dict(row)

    async def get_book_by_filename(self, filename: str) -> tuple[str, str, str] | None:
        """Get book hash, file path and name by filename (supports exact, case-insensitive and sanitized match)."""
        clean_fn = str(filename or "").strip()
        if not clean_fn:
            return None

        # 1. Exact or Case-insensitive match on dosya_adi
        cursor = await self.conn.execute(
            "SELECT dosya_hash, dosya_yolu, dosya_adi FROM kitaplar WHERE dosya_adi = ? COLLATE NOCASE LIMIT 1",
            (clean_fn,),
        )
        row = await cursor.fetchone()
        if row:
            return row

        # 2. Match sanitized filename variant (e.g. Turkish characters replaced by _)
        from app.utils import sanitize_filename

        sanitized = sanitize_filename(clean_fn)
        if sanitized and sanitized != clean_fn:
            cursor = await self.conn.execute(
                "SELECT dosya_hash, dosya_yolu, dosya_adi FROM kitaplar WHERE dosya_adi = ? COLLATE NOCASE LIMIT 1",
                (sanitized,),
            )
            row = await cursor.fetchone()
            if row:
                return row

        # 3. Match against end of dosya_yolu on disk
        cursor = await self.conn.execute(
            "SELECT dosya_hash, dosya_yolu, dosya_adi FROM kitaplar WHERE dosya_yolu LIKE ? OR dosya_yolu LIKE ? LIMIT 1",
            (f"%{clean_fn}", f"%{sanitized}"),
        )
        return await cursor.fetchone()

    async def get_stats(self) -> dict:
        """Get library statistics."""
        cat_cur = await self.conn.execute(
            "SELECT kategori, COUNT(*) as cnt FROM kitaplar GROUP BY kategori ORDER BY cnt DESC"
        )
        cat_rows = await cat_cur.fetchall()
        categories = [{"name": r["kategori"] or "Bilinmeyen", "count": r["cnt"]} for r in cat_rows]

        monthly_cur = await self.conn.execute("""
            SELECT strftime('%Y-%m', ekleme_tarihi) as ay, COUNT(*) as cnt
            FROM kitaplar
            WHERE ekleme_tarihi >= date('now', '-6 months')
            GROUP BY ay ORDER BY ay
        """)
        monthly_rows = await monthly_cur.fetchall()
        monthly = [{"month": r["ay"], "count": r["cnt"]} for r in monthly_rows]

        # Single optimized aggregate query instead of 4 separate roundtrips
        agg_cur = await self.conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN is_favorite = 1 THEN 1 END) as total_fav,
                COUNT(DISTINCT CASE WHEN yazar IS NOT NULL AND yazar != '' THEN yazar END) as unique_authors,
                COUNT(DISTINCT CASE WHEN kategori IS NOT NULL AND kategori != '' THEN kategori END) as unique_cats
            FROM kitaplar
        """)
        agg_row = await agg_cur.fetchone()
        total = agg_row["total"] if agg_row else 0
        total_fav = agg_row["total_fav"] if agg_row else 0
        unique_authors = agg_row["unique_authors"] if agg_row else 0
        unique_cats = agg_row["unique_cats"] if agg_row else 0
        top_cat = categories[0]["name"] if categories else "—"

        return {
            "categories": categories,
            "monthly": monthly,
            "general": {
                "total_books": total,
                "total_favorites": total_fav,
                "unique_authors": unique_authors,
                "unique_categories": unique_cats,
                "top_category": top_cat,
            },
        }

    async def get_collection_name(self, col_id: int) -> str:
        """Get collection name by ID."""
        cursor = await self.conn.execute("SELECT isim FROM koleksiyonlar WHERE id = ?", (col_id,))
        row = await cursor.fetchone()
        return row[0] if row else f"koleksiyon_{col_id}"

    async def get_distinct_values(self, column: str) -> list[str]:
        """Get distinct non-null values for a column from kitaplar table using fixed query mapping."""
        queries = {
            "yazar": "SELECT DISTINCT yazar FROM kitaplar WHERE yazar IS NOT NULL AND yazar != ''",
            "kategori": "SELECT DISTINCT kategori FROM kitaplar WHERE kategori IS NOT NULL AND kategori != ''",
        }
        query = queries.get(column)
        if not query:
            return []
        cursor = await self.conn.execute(query)
        return [r[0] for r in await cursor.fetchall()]

    async def get_chat_stats(self) -> str:
        """Get lightweight library profile for chat context."""
        row = await (await self.conn.execute("SELECT COUNT(*) FROM kitaplar")).fetchone()
        total_books = int(row[0]) if row else 0

        cat_cur = await self.conn.execute("""
            SELECT kategori, COUNT(*) as cnt
            FROM kitaplar
            GROUP BY kategori
            ORDER BY cnt DESC
            LIMIT 3
        """)
        cat_rows = await cat_cur.fetchall()
        cats_str = ", ".join([f"{r[0]} ({r[1]})" for r in cat_rows]) if cat_rows else "Yok"

        last_cur = await self.conn.execute("""
            SELECT kitap_adi, yazar
            FROM kitaplar
            ORDER BY ekleme_tarihi DESC
            LIMIT 3
        """)
        last_books = await last_cur.fetchall()
        last_str = ", ".join([f"{r[0]} ({r[1]})" for r in last_books]) if last_books else "Yok"

        return f"Toplam {total_books} kitap. Ağırlıklı kategoriler: {cats_str}. Son eklenenler: {last_str}."

    @staticmethod
    def _inspect_book_file_sizes(books: list[dict]) -> None:
        """Measure on-disk file size for each book record."""
        import os

        for b in books:
            path = b.get("dosya_yolu") or ""
            size = 0
            if path and os.path.exists(path):
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
            b["dosya_boyutu"] = size

    @staticmethod
    def _index_candidate_duplicates(
        books: list[dict],
    ) -> tuple[dict[tuple[str, str], list[dict]], dict[int, list[dict]]]:
        """Index books by normalized (title, author) and file size."""
        by_title_author: dict[tuple[str, str], list[dict]] = {}
        by_size: dict[int, list[dict]] = {}

        for b in books:
            title = (b.get("kitap_adi") or "").strip().lower()
            author = (b.get("yazar") or "").strip().lower()
            size = b.get("dosya_boyutu", 0)

            if len(title) > 2:
                by_title_author.setdefault((title, author), []).append(b)
            if size > 1024:
                by_size.setdefault(size, []).append(b)

        return by_title_author, by_size

    @staticmethod
    def _collect_duplicate_groups(
        by_title_author: dict[tuple[str, str], list[dict]],
        by_size: dict[int, list[dict]],
    ) -> list[dict]:
        """Collect deduplicated groups from title-author and file-size clusters."""
        duplicate_groups: list[dict] = []
        seen_group_hashes: set[frozenset[str]] = set()

        for group in by_title_author.values():
            if len(group) > 1:
                group_hashes = frozenset(b["dosya_hash"] for b in group)
                if group_hashes not in seen_group_hashes:
                    seen_group_hashes.add(group_hashes)
                    duplicate_groups.append(
                        {
                            "title": group[0].get("kitap_adi") or "Başlıksız",
                            "author": group[0].get("yazar") or "",
                            "reason": f"Aynı Eser Başlığı: '{group[0].get('kitap_adi')}'",
                            "match_type": "title_author",
                            "items": group,
                            "books": group,
                        }
                    )

        for s, group in by_size.items():
            if len(group) > 1:
                group_hashes = frozenset(b["dosya_hash"] for b in group)
                if group_hashes not in seen_group_hashes:
                    seen_group_hashes.add(group_hashes)
                    duplicate_groups.append(
                        {
                            "title": group[0].get("kitap_adi") or "Mükerrer Dosya Boyutu",
                            "author": group[0].get("yazar") or "",
                            "reason": f"Aynı Dosya Boyutu ({s // 1024} KB)",
                            "match_type": "file_size",
                            "items": group,
                            "books": group,
                        }
                    )

        return duplicate_groups

    async def find_duplicate_books(self) -> list[dict]:
        """Find duplicate books by normalized title and author, or identical file size."""
        cur = await self.conn.execute(
            """
            SELECT id, dosya_hash, dosya_adi, kitap_adi, yazar, kategori,
                   dosya_yolu, ekleme_tarihi, has_cover
            FROM kitaplar
            ORDER BY id ASC
            """
        )
        rows = await cur.fetchall()
        books = [dict(r) for r in rows]

        self._inspect_book_file_sizes(books)
        by_title_author, by_size = self._index_candidate_duplicates(books)
        return self._collect_duplicate_groups(by_title_author, by_size)
