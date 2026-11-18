"""Database management and infrastructure orchestration for Dijital Kütüphane."""

import asyncio
import os
import re
import shutil
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from app.constants import (
    ARCHIVE_DIR,
    DATA_DIR,
    LIBRARY_ROOT,
    STANDARD_CATEGORIES,
    THUMBNAILS_DIR,
)
from app.repositories.document_repository import DocumentRepository
from app.utils import is_path_within, resolve_portable_book_path

DB_PATH = os.path.join(DATA_DIR, "kutuphane.db")


class DatabaseManager(DocumentRepository):
    """Concrete DatabaseManager inheriting pure CRUD from DocumentRepository and adding app-level orchestration."""

    # ------------------------------------------------------------------
    # Infrastructure & Orchestration overrides / helpers
    # ------------------------------------------------------------------

    async def add_book(self, data: dict) -> None:
        """Add a book to database and trigger automatic category normalization (Orchestration)."""
        await super().add_book(data)
        # Immediate normalization for the new book (Business logic / Orchestration)
        await self._auto_clean_categories(data.get("dosya_hash"))

    @staticmethod
    def _delete_thumbnails(file_hash: str) -> None:
        """Delete thumbnail files (.jpg and legacy .webp) associated with book."""
        from app.logger import log_event

        for ext in (".jpg", ".webp"):
            thumb_path = os.path.join(THUMBNAILS_DIR, f"{file_hash}{ext}")
            if os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except FileNotFoundError:
                    log_event(
                        "filesystem",
                        "DEBUG",
                        "Thumbnail zaten silinmiş veya bulunamadı",
                        file_hash=file_hash,
                    )
                except OSError as e:
                    log_event(
                        "filesystem",
                        "ERROR",
                        f"Thumbnail silinirken OS hatası: {e}",
                        file_hash=file_hash,
                    )

    @staticmethod
    def _delete_cached_text(file_path: str) -> None:
        """Delete cached full-text extraction files if present."""
        from app.logger import log_event

        for suffix in (".full.txt", ".txt"):
            txt_file = file_path + suffix
            if os.path.exists(txt_file):
                try:
                    os.remove(txt_file)
                except OSError as e:
                    log_event(
                        "filesystem",
                        "DEBUG",
                        f"Cached text cleanup warning ({txt_file}): {e}",
                    )

    @staticmethod
    def _clean_empty_parent_dirs(current_dir: str, levels: int = 2) -> None:
        """Clean empty parent folders up to specified depth."""
        from app.logger import log_event

        for _ in range(levels):
            try:
                if os.path.exists(current_dir) and not os.listdir(current_dir):
                    os.rmdir(current_dir)
                    log_event(
                        "filesystem",
                        "INFO",
                        f"Boş klasör temizlendi: {current_dir}",
                    )
                    current_dir = os.path.dirname(current_dir)
                else:
                    break
            except OSError as e:
                log_event(
                    "filesystem",
                    "WARNING",
                    f"Boş klasör temizlenirken OS/Dosya sistemi hatası: {e}",
                )

    def _archive_physical_file(self, file_path: str, raise_on_lock: bool = False) -> None:
        """Archive book physical file into silinenler folder and cleanup empty dirs."""
        from app.logger import log_event

        try:
            abs_file_path = os.path.realpath(os.path.abspath(file_path))
            if not is_path_within(LIBRARY_ROOT, abs_file_path):
                log_event(
                    "security",
                    "ERROR",
                    "Kütüphane dışı dosya arşivleme engellendi",
                    path=abs_file_path,
                )
                return

            rel = os.path.relpath(abs_file_path, LIBRARY_ROOT)
            archive_path = os.path.join(ARCHIVE_DIR, "silinenler", rel)
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            if os.path.exists(archive_path):
                stem, ext = os.path.splitext(archive_path)
                archive_path = f"{stem}_{int(time.time())}{ext}"
            shutil.move(abs_file_path, archive_path)

            log_event(
                "filesystem",
                "INFO",
                "Kitap arşive taşındı",
                original=abs_file_path,
                archived=archive_path,
            )
            self._clean_empty_parent_dirs(os.path.dirname(abs_file_path), levels=2)
        except FileNotFoundError as e:
            log_event(
                "filesystem",
                "DEBUG",
                f"Arşivlenecek fiziksel dosya bulunamadı: {e}",
            )
        except PermissionError as e:
            log_event(
                "filesystem",
                "ERROR",
                f"Dosya kullanımda olduğu için arşive taşınamadı: {e}",
            )
            if raise_on_lock:
                raise
        except OSError as e:
            log_event(
                "filesystem",
                "ERROR",
                f"Dosya arşive taşınırken OS/Erişim hatası: {e}",
            )
            if raise_on_lock and getattr(e, "winerror", None) == 32:
                raise PermissionError(str(e)) from e
        except Exception as e:
            log_event("filesystem", "ERROR", f"Dosya arşivlenirken beklenmedik hata: {e}")

    async def get_book_path(self, file_hash: str) -> tuple[str, str] | None:
        """Get portable resolved file path and name for a book by its hash."""
        row = await super().get_book_path(file_hash)
        if not row:
            return None
        resolved_path = resolve_portable_book_path(row[0], LIBRARY_ROOT)
        return (resolved_path, row[1])

    async def get_book_by_hash(self, file_hash: str) -> dict | None:
        """Get complete book metadata record by hash with portable path resolution."""
        book = await super().get_book_by_hash(file_hash)
        if not book:
            return None
        if book.get("dosya_yolu"):
            book["dosya_yolu"] = resolve_portable_book_path(book["dosya_yolu"], LIBRARY_ROOT)
        return book

    async def delete_book(self, file_hash: str) -> None:
        """Delete a book safely: archive physical file FIRST (preventing DB/disk desync on lock), then remove DB records & artifacts."""
        file_path = None
        cursor = await self.conn.execute(
            "SELECT dosya_yolu FROM kitaplar WHERE dosya_hash = ?", (file_hash,)
        )
        row = await cursor.fetchone()
        if row and row[0]:
            file_path = resolve_portable_book_path(row[0], LIBRARY_ROOT)

        # 1. Move physical file first so a Windows file lock aborts cleanly before deleting notes/metadata
        if file_path and os.path.exists(file_path):
            await asyncio.to_thread(self._archive_physical_file, file_path, True)

        # 2. Delete SQLite rows and indices
        await super().delete_book(file_hash)

        # 3. Delete thumbnails & cached full-text files off the event loop
        await asyncio.to_thread(self._delete_thumbnails, file_hash)
        if file_path:
            await asyncio.to_thread(self._delete_cached_text, file_path)

    # ------------------------------------------------------------------
    # Category normalization (Business rules)
    # ------------------------------------------------------------------

    @staticmethod
    def _match_standard_category(current_cat: str) -> str:
        """Match a category string to standard taxonomy or fallback."""
        if current_cat in STANDARD_CATEGORIES:
            return current_cat

        norm_current = re.sub(r"[^\w\s]", "", current_cat.lower())
        norm_current = re.sub(r"\s+", " ", norm_current).strip()

        for std_cat in STANDARD_CATEGORIES:
            norm_std = re.sub(r"[^\w\s]", "", std_cat.lower())
            norm_std = re.sub(r"\s+", " ", norm_std).strip()
            if norm_current == norm_std:
                return std_cat

        for std_cat in STANDARD_CATEGORIES:
            if current_cat.lower() in std_cat.lower() or std_cat.lower() in current_cat.lower():
                return std_cat

        if len(current_cat) > 25 or "/" in current_cat or "," in current_cat:
            return "Araştırma, İnceleme ve Eleştiri"

        return current_cat

    async def _auto_clean_categories(self, target_hash: str | None = None) -> None:
        """Normalize category names to standard list. If target_hash is provided, cleans only that book."""
        if target_hash:
            cursor = await self.conn.execute(
                "SELECT dosya_hash, kategori, alt_kategori FROM kitaplar WHERE dosya_hash = ?",
                (target_hash,),
            )
        else:
            cursor = await self.conn.execute(
                "SELECT dosya_hash, kategori, alt_kategori FROM kitaplar"
            )

        updates = []
        for row in await cursor.fetchall():
            file_hash, cat, subcat = row
            if not cat:
                continue

            current_cat = str(cat).strip()
            new_subcat = str(subcat or "").strip()
            matched_cat = self._match_standard_category(current_cat)

            if matched_cat != cat or new_subcat != subcat:
                from app.logger import log_event

                log_event(
                    "database",
                    "INFO",
                    f"Kategori normalize edildi: {cat} -> {matched_cat}",
                    file_hash=file_hash,
                )
                updates.append((matched_cat, new_subcat, file_hash))

        if updates:
            await self.conn.executemany(
                "UPDATE kitaplar SET kategori = ?, alt_kategori = ? WHERE dosya_hash = ?",
                updates,
            )
            await self.conn.commit()


_tables_initialized = False


async def init_db_schema() -> None:
    """Run table and index creation once at application startup and configure WAL mode."""
    global _tables_initialized
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode = WAL;")
        await conn.execute("PRAGMA busy_timeout = 10000;")
        await conn.execute("PRAGMA synchronous = NORMAL;")
        await conn.execute("PRAGMA foreign_keys = ON;")
        await _ensure_tables(conn)
    _tables_initialized = True


async def _create_schema_tables(conn: aiosqlite.Connection) -> None:
    """Create initial schema tables and virtual FTS5 tables if they don't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kitaplar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kitap_adi TEXT,
            yazar TEXT,
            kategori TEXT,
            alt_kategori TEXT,
            ozet TEXT,
            anahtar_kelimeler TEXT,
            dosya_adi TEXT,
            dosya_hash TEXT UNIQUE,
            dosya_yolu TEXT,
            is_favorite BOOLEAN DEFAULT 0,
            okunulan_sayfa INTEGER DEFAULT 0,
            sira_numarasi INTEGER DEFAULT 999999,
            has_cover BOOLEAN DEFAULT 0,
            sayfa_sayisi INTEGER DEFAULT 0,
            dosya_boyutu INTEGER DEFAULT 0,
            ekleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS koleksiyonlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT UNIQUE,
            is_dynamic BOOLEAN DEFAULT 0,
            rule_json TEXT DEFAULT NULL
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kitap_toc (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_hash TEXT NOT NULL,
            title TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            target_page INTEGER NOT NULL,
            level INTEGER DEFAULT 1,
            source TEXT DEFAULT 'native',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dosya_hash) REFERENCES kitaplar(dosya_hash) ON DELETE CASCADE
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS koleksiyon_kitap (
            koleksiyon_id INTEGER,
            kitap_hash TEXT,
            PRIMARY KEY (koleksiyon_id, kitap_hash),
            FOREIGN KEY (koleksiyon_id) REFERENCES koleksiyonlar(id) ON DELETE CASCADE,
            FOREIGN KEY (kitap_hash) REFERENCES kitaplar(dosya_hash) ON DELETE CASCADE
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kitap_notlari (
            id TEXT PRIMARY KEY,
            dosya_hash TEXT NOT NULL,
            sayfa_no INTEGER NOT NULL,
            secilen_metin TEXT,
            not_metni TEXT,
            renk_hex TEXT DEFAULT '#fef08a',
            renk_sinif TEXT DEFAULT 'yellow',
            koordinatlar TEXT,
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dosya_hash) REFERENCES kitaplar(dosya_hash) ON DELETE CASCADE
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS durable_jobs (
            id TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            message TEXT DEFAULT '',
            error TEXT DEFAULT '',
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kitap_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_hash TEXT NOT NULL,
            sayfa_no INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            metin TEXT NOT NULL,
            char_count INTEGER NOT NULL,
            embedding BLOB,
            embedding_model TEXT DEFAULT 'hash-v1',
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dosya_hash) REFERENCES kitaplar(dosya_hash) ON DELETE CASCADE
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kitap_ocr_sayfalar (
            dosya_hash TEXT NOT NULL,
            sayfa_no INTEGER NOT NULL,
            img_w INTEGER NOT NULL DEFAULT 0,
            img_h INTEGER NOT NULL DEFAULT 0,
            words_json TEXT NOT NULL DEFAULT '[]',
            full_text TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (dosya_hash, sayfa_no)
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kitap_yer_imleri (
            dosya_hash TEXT NOT NULL,
            sayfa_no INTEGER NOT NULL,
            etiket TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (dosya_hash, sayfa_no)
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS okuma_oturumlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_hash TEXT NOT NULL,
            tarih_gun TEXT NOT NULL,
            sure_saniye INTEGER NOT NULL DEFAULT 0,
            okunan_sayfa_sayisi INTEGER NOT NULL DEFAULT 0,
            baslangic_sayfa INTEGER DEFAULT 1,
            bitis_sayfa INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dosya_hash, tarih_gun)
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS srs_kartlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_hash TEXT NOT NULL,
            not_id TEXT,
            sayfa_no INTEGER DEFAULT 1,
            on_yuz TEXT NOT NULL,
            arka_yuz TEXT NOT NULL,
            baglam TEXT DEFAULT '',
            durum INTEGER DEFAULT 0,
            stability REAL DEFAULT 0.0,
            difficulty REAL DEFAULT 5.0,
            reps INTEGER DEFAULT 0,
            lapses INTEGER DEFAULT 0,
            scheduled_days INTEGER DEFAULT 0,
            elapsed_days INTEGER DEFAULT 0,
            last_review TEXT,
            due_at TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS kitap_chunks_fts USING fts5(
            dosya_hash UNINDEXED,
            sayfa_no UNINDEXED,
            chunk_index UNINDEXED,
            metin,
            tokenize='unicode61'
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kg_entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            description TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kg_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            source_evidence TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


async def _apply_has_cover_migration(conn: aiosqlite.Connection) -> None:
    """Migration 2: add has_cover column and populate from thumbnails directory."""
    cur = await conn.execute("PRAGMA table_info(kitaplar)")
    existing_cols = [row[1] for row in await cur.fetchall()]
    if "has_cover" not in existing_cols:
        await conn.execute("ALTER TABLE kitaplar ADD COLUMN has_cover BOOLEAN DEFAULT 0")
        if os.path.exists(THUMBNAILS_DIR):
            for fname in os.listdir(THUMBNAILS_DIR):
                if fname.lower().endswith((".jpg", ".webp")):
                    h, _ = os.path.splitext(fname)
                    await conn.execute(
                        "UPDATE kitaplar SET has_cover = 1 WHERE dosya_hash = ?",
                        (h,),
                    )
    await conn.execute(
        "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (2, 'add_has_cover_column')"
    )


async def _run_migrations(conn: aiosqlite.Connection) -> None:
    """Run incremental database schema migrations."""
    cur = await conn.execute("SELECT version FROM schema_migrations")
    applied_versions = {row[0] for row in await cur.fetchall()}

    if 1 not in applied_versions:
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (1, 'initial_schema')"
        )

    if 2 not in applied_versions:
        await _apply_has_cover_migration(conn)

    if 3 not in applied_versions:
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (3, 'durable_jobs_table')"
        )

    if 4 not in applied_versions:
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (4, 'kitap_chunks_fts_tables')"
        )

    if 5 not in applied_versions:
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (5, 'kg_triplestore_tables')"
        )

    if 6 not in applied_versions:
        cur = await conn.execute("PRAGMA table_info(koleksiyonlar)")
        col_names = [row[1] for row in await cur.fetchall()]
        if "is_dynamic" not in col_names:
            await conn.execute("ALTER TABLE koleksiyonlar ADD COLUMN is_dynamic BOOLEAN DEFAULT 0")
        if "rule_json" not in col_names:
            await conn.execute("ALTER TABLE koleksiyonlar ADD COLUMN rule_json TEXT DEFAULT NULL")
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (6, 'toc_and_dynamic_collections')"
        )

    if 7 not in applied_versions:
        cur = await conn.execute("PRAGMA table_info(kitaplar)")
        book_cols = {row[1] for row in await cur.fetchall()}
        if "sayfa_sayisi" not in book_cols:
            await conn.execute("ALTER TABLE kitaplar ADD COLUMN sayfa_sayisi INTEGER DEFAULT 0")
        if "dosya_boyutu" not in book_cols:
            await conn.execute("ALTER TABLE kitaplar ADD COLUMN dosya_boyutu INTEGER DEFAULT 0")
        await conn.execute("""
            UPDATE kitaplar
            SET sayfa_sayisi = COALESCE(
                (SELECT MAX(sayfa_no) FROM kitap_chunks WHERE kitap_chunks.dosya_hash = kitaplar.dosya_hash),
                0
            )
            WHERE COALESCE(sayfa_sayisi, 0) = 0
        """)
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (7, 'add_page_count_and_file_size')"
        )

    if 8 not in applied_versions:
        cur = await conn.execute("PRAGMA table_info(kitap_chunks)")
        chunk_cols = {row[1] for row in await cur.fetchall()}
        if "embedding_model" not in chunk_cols:
            await conn.execute(
                "ALTER TABLE kitap_chunks ADD COLUMN embedding_model TEXT DEFAULT 'hash-v1'"
            )
        await conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version, name) VALUES (8, 'rd_v8_embeddings_ocr_bookmarks_srs')"
        )


async def _create_indexes(conn: aiosqlite.Connection) -> None:
    """Create indexes across tables for high-performance lookups."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_hash ON kitaplar(dosya_hash)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_kategori ON kitaplar(kategori)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_favorite ON kitaplar(is_favorite)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_yazar ON kitaplar(yazar)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_sira ON kitaplar(sira_numarasi)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_has_cover ON kitaplar(has_cover)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_tarih ON kitaplar(ekleme_tarihi)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_sira_tarih ON kitaplar(sira_numarasi ASC, ekleme_tarihi DESC)",
        "CREATE INDEX IF NOT EXISTS idx_kitaplar_dosya_adi_nocase ON kitaplar(dosya_adi COLLATE NOCASE)",
        "CREATE INDEX IF NOT EXISTS idx_koleksiyon_kitap_hash ON koleksiyon_kitap(kitap_hash)",
        "CREATE INDEX IF NOT EXISTS idx_koleksiyon_kitap_id ON koleksiyon_kitap(koleksiyon_id)",
        "CREATE INDEX IF NOT EXISTS idx_kitap_notlari_hash ON kitap_notlari(dosya_hash)",
        "CREATE INDEX IF NOT EXISTS idx_kitap_notlari_sayfa ON kitap_notlari(dosya_hash, sayfa_no)",
        "CREATE INDEX IF NOT EXISTS idx_kitap_chunks_hash_sayfa ON kitap_chunks(dosya_hash, sayfa_no)",
        "CREATE INDEX IF NOT EXISTS idx_durable_jobs_status_sched ON durable_jobs(status, scheduled_at)",
        "CREATE INDEX IF NOT EXISTS idx_durable_jobs_type ON durable_jobs(job_type)",
        "CREATE INDEX IF NOT EXISTS idx_kg_entities_type ON kg_entities(entity_type)",
        "CREATE INDEX IF NOT EXISTS idx_kg_entities_name ON kg_entities(name)",
        "CREATE INDEX IF NOT EXISTS idx_kg_relations_src ON kg_relations(source_id)",
        "CREATE INDEX IF NOT EXISTS idx_kg_relations_tgt ON kg_relations(target_id)",
        "CREATE INDEX IF NOT EXISTS idx_kg_relations_type ON kg_relations(relation_type)",
        "CREATE INDEX IF NOT EXISTS idx_kitap_toc_hash ON kitap_toc(dosya_hash)",
        "CREATE INDEX IF NOT EXISTS idx_kitap_ocr_hash ON kitap_ocr_sayfalar(dosya_hash)",
        "CREATE INDEX IF NOT EXISTS idx_kitap_yer_imleri_hash ON kitap_yer_imleri(dosya_hash)",
        "CREATE INDEX IF NOT EXISTS idx_okuma_oturumlari_tarih ON okuma_oturumlari(tarih_gun)",
        "CREATE INDEX IF NOT EXISTS idx_okuma_oturumlari_hash ON okuma_oturumlari(dosya_hash)",
        "CREATE INDEX IF NOT EXISTS idx_srs_kartlari_due ON srs_kartlari(due_at)",
        "CREATE INDEX IF NOT EXISTS idx_srs_kartlari_hash ON srs_kartlari(dosya_hash)",
    ]
    for idx_sql in indexes:
        await conn.execute(idx_sql)
    await conn.commit()


async def _ensure_tables(conn: aiosqlite.Connection) -> None:
    """Create all required tables and indexes if they don't exist and run light migrations."""
    await _create_schema_tables(conn)
    await _run_migrations(conn)
    await _create_indexes(conn)


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[DatabaseManager, None]:
    """Context manager to yield a DatabaseManager instance with connection-level PRAGMAs configured."""
    global _tables_initialized
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        # Connection-level PRAGMAs must be set for each connection
        await conn.execute("PRAGMA busy_timeout = 10000;")
        await conn.execute("PRAGMA synchronous = NORMAL;")
        await conn.execute("PRAGMA foreign_keys = ON;")
        if not _tables_initialized:
            await conn.execute("PRAGMA journal_mode = WAL;")
            await _ensure_tables(conn)
            _tables_initialized = True
        yield DatabaseManager(conn)


def _prune_old_backups(backup_dir: str, max_backups: int) -> None:
    """Enforce retention policy: keep the newest max_backups backup files."""
    if max_backups <= 0 or not os.path.exists(backup_dir):
        return
    try:
        backups = [
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.startswith("kutuphane_backup_") and f.endswith(".db")
        ]
        backups.sort(key=os.path.getmtime, reverse=True)
        for old_backup in backups[max_backups:]:
            try:
                os.remove(old_backup)
            except OSError as e:
                from app.logger import log_event

                log_event(
                    "database",
                    "DEBUG",
                    f"Old backup removal warning ({old_backup}): {e}",
                )
    except Exception as e:
        from app.logger import log_event

        log_event("database", "DEBUG", f"Backup retention check warning: {e}")


_FORBIDDEN_PATH_CHARS = frozenset('<>:"|?*')


def _has_control_or_forbidden_chars(segment: str) -> bool:
    """Return True if a resolved path segment contains control or forbidden filename characters."""
    return any(ord(ch) < 32 or ch in _FORBIDDEN_PATH_CHARS for ch in segment)


def _validate_backup_path(backup_path: str | os.PathLike[str] | None, backup_dir: Path) -> Path:
    """Resolve and validate a backup database path compatibly with Windows drives and POSIX paths."""
    from datetime import datetime

    if backup_path is None:
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = backup_dir / f"kutuphane_backup_{ts_str}.db"
    else:
        raw_str = os.fspath(backup_path)
        if not raw_str.strip() or any(ord(ch) < 32 for ch in raw_str):
            raise ValueError("Geçersiz yedekleme dosya yolu.")
        target = Path(raw_str)

    try:
        resolved = target.expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError("Geçersiz yedekleme dosya yolu.") from exc

    if resolved.suffix.lower() != ".db":
        raise ValueError("Yedekleme dosya uzantısı .db olmalıdır.")

    # Validate path segments after anchor/drive (e.g. 'D:\\' or '/') so Windows drive colons are permitted.
    segments = resolved.parts[1:] if resolved.anchor else resolved.parts
    if not segments or any(_has_control_or_forbidden_chars(seg) for seg in segments):
        raise ValueError("Yedekleme dosya yolu geçersiz karakterler içeriyor.")

    return resolved


async def create_database_backup(backup_path: str | os.PathLike[str] | None = None, max_backups: int = 5) -> str:
    """Create a consistent point-in-time snapshot backup of the library database with retention policy."""
    backup_dir = Path(DB_PATH).resolve(strict=False).parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    resolved_backup = _validate_backup_path(backup_path, backup_dir)
    resolved_backup.parent.mkdir(parents=True, exist_ok=True)

    if resolved_backup.exists():
        try:
            resolved_backup.unlink(missing_ok=True)
        except OSError as e:
            from app.logger import log_event

            log_event("database", "DEBUG", f"Previous backup file removal warning: {e}")

    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("VACUUM INTO ?", (str(resolved_backup),))

    _prune_old_backups(str(backup_dir), max_backups)
    return str(resolved_backup)
