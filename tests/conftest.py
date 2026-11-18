import os
import shutil
import tempfile

# -----------------------------------------------------------------------------
# CRITICAL IMPORT-TIME PATCH:
# To prevent ChromaDB and FileSystem operations from touching the real, live
# "veriler" directory during pytest run, we dynamically override all directory
# constants in app.constants BEFORE importing any other application module.
# -----------------------------------------------------------------------------
TEST_TEMP_DIR = tempfile.mkdtemp(prefix="dijital_kutuphane_global_test_")
os.environ["DATA_DIR"] = TEST_TEMP_DIR
os.environ["SESSION_SECRET"] = "test-secret-key-for-testing"
os.environ["ACCESS_PASSWORD"] = ""
os.environ["ADMIN_TOKEN"] = ""

import app.constants  # noqa: E402

app.constants.DATA_DIR = TEST_TEMP_DIR
app.constants.ARCHIVE_DIR = os.path.join(TEST_TEMP_DIR, "Kaldirilmis_PDFler")
app.constants.LIBRARY_ROOT = os.path.realpath(
    os.path.abspath(os.path.join(TEST_TEMP_DIR, "Dijital_Kutuphane"))
)
app.constants.THUMBNAILS_DIR = os.path.realpath(
    os.path.abspath(os.path.join(TEST_TEMP_DIR, "thumbnails"))
)

import app.config  # noqa: E402
import app.database  # noqa: E402

app.database.DB_PATH = os.path.join(TEST_TEMP_DIR, "kutuphane.db")
app.config.CONFIG_PATH = os.path.join(TEST_TEMP_DIR, "config.json")
app.config._cached_config = None
app.config._cached_config_mtime = 0.0

os.makedirs(app.constants.ARCHIVE_DIR, exist_ok=True)
os.makedirs(app.constants.THUMBNAILS_DIR, exist_ok=True)
os.makedirs(os.path.join(TEST_TEMP_DIR, "logs"), exist_ok=True)

from collections.abc import AsyncGenerator  # noqa: E402

import aiosqlite  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402

import app.database as app_database  # noqa: E402
from app.database import DatabaseManager  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    yield TEST_TEMP_DIR
    # Cleanup after all tests
    shutil.rmtree(TEST_TEMP_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def mock_env(test_data_dir):
    """Set up mock environment variables for absolute isolation."""
    # Since DB_PATH is initialized using DATA_DIR at import-time,
    # it is already pointing to an isolated file in TEST_TEMP_DIR.
    # No dynamic mutation is needed, avoiding reference mismatch bugs!
    return None


@pytest.fixture(autouse=True)
def init_test_db():
    """Automatically initialize tables in the isolated test DB file before tests run (synchronously).

    Using a synchronous autouse fixture ensures seamless compatibility with both sync and async tests,
    preventing PytestRemovedIn9Warning or PytestUnhandledCoroutine errors.
    """
    db_file = app_database.DB_PATH

    from app.auth import AUTH_STATE
    from app.logger import LOG_BUFFER
    from app.tasks import active_tasks

    AUTH_STATE["attempts"].clear()
    AUTH_STATE["valid_tokens"].clear()
    active_tasks.clear()
    LOG_BUFFER.clear()

    # Ensure parent folder exists
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    # Connect and initialize schema using standard sqlite3
    import sqlite3

    conn = sqlite3.connect(db_file)
    try:
        conn.execute("""
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
                okunulan_sayfa INTEGER DEFAULT 1,
                sayfa_sayisi INTEGER DEFAULT 0,
                dosya_boyutu INTEGER DEFAULT 0,
                sira_numarasi INTEGER DEFAULT 999999,
                has_cover BOOLEAN DEFAULT 0,
                ekleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS koleksiyonlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT UNIQUE,
                is_dynamic BOOLEAN DEFAULT 0,
                rule_json TEXT DEFAULT NULL
            )
        """)
        conn.execute("""
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS koleksiyon_kitap (
                koleksiyon_id INTEGER,
                kitap_hash TEXT,
                PRIMARY KEY (koleksiyon_id, kitap_hash),
                FOREIGN KEY (koleksiyon_id) REFERENCES koleksiyonlar(id) ON DELETE CASCADE,
                FOREIGN KEY (kitap_hash) REFERENCES kitaplar(dosya_hash) ON DELETE CASCADE
            )
        """)

        conn.execute("""
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
        conn.execute("""
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
        conn.execute("""
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
        conn.execute("""
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kitap_yer_imleri (
                dosya_hash TEXT NOT NULL,
                sayfa_no INTEGER NOT NULL,
                etiket TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (dosya_hash, sayfa_no)
            )
        """)
        conn.execute("""
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
        conn.execute("""
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
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS kitap_chunks_fts USING fts5(
                dosya_hash UNINDEXED,
                sayfa_no UNINDEXED,
                chunk_index UNINDEXED,
                metin,
                tokenize='unicode61'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                description TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
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

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kitaplar_hash ON kitaplar(dosya_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kitaplar_kategori ON kitaplar(kategori)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kitaplar_favorite ON kitaplar(is_favorite)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kitaplar_yazar ON kitaplar(yazar)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kitaplar_sira ON kitaplar(sira_numarasi)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kitaplar_tarih ON kitaplar(ekleme_tarihi)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kitaplar_sira_tarih ON kitaplar(sira_numarasi ASC, ekleme_tarihi DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kitaplar_dosya_adi_nocase ON kitaplar(dosya_adi COLLATE NOCASE)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_koleksiyon_kitap_hash ON koleksiyon_kitap(kitap_hash)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_koleksiyon_kitap_id ON koleksiyon_kitap(koleksiyon_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kitap_notlari_hash ON kitap_notlari(dosya_hash)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kitap_notlari_sayfa ON kitap_notlari(dosya_hash, sayfa_no)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kitap_chunks_hash_sayfa ON kitap_chunks(dosya_hash, sayfa_no)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_durable_jobs_status_sched ON durable_jobs(status, scheduled_at)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_durable_jobs_type ON durable_jobs(job_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_entities_type ON kg_entities(entity_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_entities_name ON kg_entities(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_relations_src ON kg_relations(source_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kg_relations_tgt ON kg_relations(target_id)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_kg_relations_type ON kg_relations(relation_type)"
        )
        conn.commit()
    finally:
        conn.close()

    yield

    # Clean up test DB tables after each test to ensure isolation
    conn = sqlite3.connect(db_file)
    try:
        conn.execute("DROP TABLE IF EXISTS kitap_ocr_sayfalar")
        conn.execute("DROP TABLE IF EXISTS kitap_yer_imleri")
        conn.execute("DROP TABLE IF EXISTS okuma_oturumlari")
        conn.execute("DROP TABLE IF EXISTS srs_kartlari")
        conn.execute("DROP TABLE IF EXISTS kitap_toc")
        conn.execute("DROP TABLE IF EXISTS kg_relations")
        conn.execute("DROP TABLE IF EXISTS kg_entities")
        conn.execute("DROP TABLE IF EXISTS kitaplar")
        conn.execute("DROP TABLE IF EXISTS koleksiyonlar")
        conn.execute("DROP TABLE IF EXISTS koleksiyon_kitap")
        conn.execute("DROP TABLE IF EXISTS kitap_notlari")
        conn.execute("DROP TABLE IF EXISTS durable_jobs")
        conn.execute("DROP TABLE IF EXISTS kitap_chunks_fts")
        conn.execute("DROP TABLE IF EXISTS kitap_chunks")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
async def temp_db_conn() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Provide a raw connection to the active isolated test database."""
    async with aiosqlite.connect(app_database.DB_PATH) as conn:
        yield conn


@pytest.fixture
async def temp_db(temp_db_conn) -> DatabaseManager:
    """Provide a DatabaseManager wrapping the active isolated test connection."""
    return DatabaseManager(temp_db_conn)


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an AsyncClient connecting to our isolated test app environment."""
    # Wrap in ASGITransport to match modern httpx specifications
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_pdf_bytes():
    """Return sample PDF bytes for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000262 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n355\n%%EOF"


@pytest.fixture
def sample_book_data():
    """Return sample book metadata."""
    return {
        "kitap_adi": "Test Kitabı",
        "yazar": "Test Yazar",
        "kategori": "Bilim ve Teknoloji",
        "alt_kategori": "Yapay Zeka",
        "ozet": "Bu bir test kitabıdır.",
        "anahtar_kelimeler": "test, ai, yapay zeka",
        "dosya_adi": "test_kitabi.pdf",
        "dosya_hash": "abc123def456",
        "dosya_yolu": "/test/path/test_kitabi.pdf",
    }
