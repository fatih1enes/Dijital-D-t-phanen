# cspell:disable
"""Test suite verifying all fixes from Audit Report v2:
- Telegram Path Traversal protection
- esc() hardening (backtick and dollar escaping)
- Settings telegram_api_hash masking and preservation
- Telegram transient API key non-persistence
- EPUB zip decompression bomb protection
- Gemini BookSession close and eviction cloud cleanup
- OCR streaming and safe fallback limit
- .gitignore session file rules
"""

import io
import os
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import CONFIG_DEFAULTS
from app.constants import PROJECT_ROOT
from app.utils import is_path_within, sanitize_filename

# ---------------------------------------------------------------------------
# 1. Telegram Path Traversal Protection
# ---------------------------------------------------------------------------


def test_telegram_filename_sanitization():
    """Verify that malicious path traversal filenames are stripped of traversal sequences."""
    malicious_names = [
        "../../evil.pdf",
        "..\\..\\windows_evil.pdf",
        "nested/dir/document.pdf",
        "/etc/passwd.pdf",
    ]
    for name in malicious_names:
        raw_basename = os.path.basename(name)
        safe = sanitize_filename(raw_basename)
        assert ".." not in safe
        assert "/" not in safe
        assert "\\" not in safe
        assert safe.endswith(".pdf")


def test_telegram_path_containment():
    """Verify is_path_within rejects paths that attempt to escape TEMP_TELEGRAM_DIR."""
    from app.services.telegram_service import TEMP_TELEGRAM_DIR

    legit_path = os.path.join(TEMP_TELEGRAM_DIR, "tg_123_abc_book.pdf")
    assert is_path_within(TEMP_TELEGRAM_DIR, legit_path) is True

    traversal_path = os.path.join(TEMP_TELEGRAM_DIR, "..", "escape.pdf")
    assert is_path_within(TEMP_TELEGRAM_DIR, traversal_path) is False


# ---------------------------------------------------------------------------
# 2. XSS & esc() Template Literal / Backtick Hardening
# ---------------------------------------------------------------------------


def test_esc_hardening_backtick_and_dollar():
    """Verify esc() properly escapes backticks and dollar signs to prevent DOM-based XSS."""
    # Reading api.js implementation to ensure JS regex logic matches test expectation
    api_js_path = os.path.join(PROJECT_ROOT, "static", "js", "api.js")
    with open(api_js_path, encoding="utf-8") as f:
        content = f.read()

    assert '.replaceAll("`", "&#096;")' in content or '.replace(/`/g, "&#096;")' in content
    assert '.replaceAll("$", "&#036;")' in content or '.replace(/\\$/g, "&#036;")' in content
    assert "Fail-safe: If DOMPurify is unavailable" in content


def test_ui_workspace_direct_event_binding():
    """Verify ui_workspace.js uses direct event listeners instead of backtick template literal string injection."""
    ws_js_path = os.path.join(PROJECT_ROOT, "static", "js", "ui_workspace.js")
    with open(ws_js_path, encoding="utf-8") as f:
        content = f.read()

    # Ensure dangerous onclick with backticks was completely removed
    assert "editExistingNote('${hl.id}', `\\${esc(hl.text)}`" not in content
    assert "btn-edit-note" in content
    assert "editBtn.addEventListener('click'" in content


# ---------------------------------------------------------------------------
# 3. Settings: telegram_api_hash Masking and Preservation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settings_telegram_api_hash_masking():
    """Verify GET /api/settings masks telegram_api_hash with dots."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    # Mock load_config to return an unmasked hash
    mock_cfg = dict(CONFIG_DEFAULTS)
    mock_cfg["telegram_api_hash"] = "secret_tele_hash_12345"
    mock_cfg["ai_api_key"] = f"AIzaSy{'TestKey' * 3}"

    with patch("app.routers.settings.load_config", return_value=mock_cfg):
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_api_hash"] == "••••••••"
        assert data["has_telegram_hash"] is True
        assert data["ai_api_key"] == "••••••••"


@pytest.mark.asyncio
async def test_settings_telegram_api_hash_preservation():
    """Verify POST /api/settings preserves original telegram_api_hash when masked value is submitted."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    saved_calls = []

    mock_current = dict(CONFIG_DEFAULTS)
    mock_current["telegram_api_hash"] = "my_original_hash_999"

    def fake_save(cfg):
        saved_calls.append(dict(cfg))

    with (
        patch("app.routers.settings.load_config", return_value=mock_current),
        patch("app.routers.settings.save_config", side_effect=fake_save),
    ):
        # Submitting with masked hash (as sent by UI)
        response = client.post(
            "/api/settings", json={"telegram_api_hash": "••••••••", "max_pages": 15}
        )
        assert response.status_code == 200
        assert len(saved_calls) == 1
        assert saved_calls[0]["telegram_api_hash"] == "my_original_hash_999"
        assert saved_calls[0]["max_pages"] == 15


# ---------------------------------------------------------------------------
# 4. Telegram Transient Key Non-Persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_telegram_transient_key_not_saved_to_disk():
    """Verify providing a transient X-AI-Key does not call save_config in telegram endpoints."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    mock_save = MagicMock()

    with (
        patch("app.config.save_config", mock_save),
        patch("app.services.telegram_service.telegram_service.sync_documents", AsyncMock()),
    ):
        response = client.post(
            "/api/telegram/sync",
            headers={"X-AI-Key": f"AIzaSy{'HeaderKey' * 3}"},
            json={"chat_target": "me"},
        )
        assert response.status_code == 200
        # save_config must NOT be called to persist the transient header key
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# 5. EPUB Zip Bomb & Decompression Ceiling Protection
# ---------------------------------------------------------------------------


def test_epub_safe_read_zip_entry_rejects_oversized_entries():
    """Verify safe_read_zip_entry rejects files exceeding max_bytes limit."""
    from app.epub import safe_read_zip_entry

    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("normal.txt", "small file")
        z.writestr("huge.txt", b"x" * 500)

    bio.seek(0)
    with zipfile.ZipFile(bio, "r") as z:
        normal = safe_read_zip_entry(z, "normal.txt", max_bytes=1024)
        assert normal == b"small file"

        huge = safe_read_zip_entry(z, "huge.txt", max_bytes=200)
        assert huge is None  # 500 bytes exceeds 200 bytes max_bytes, must be rejected


# ---------------------------------------------------------------------------
# 6. Gemini BookSession Cloud Deletion on Eviction
# ---------------------------------------------------------------------------


def test_gemini_book_session_close_deletes_remote_file():
    """Verify BookSession.close() invokes client.files.delete()."""
    from app.services.session_manager import BookSession

    sess = BookSession("hash123", "dummy.pdf", "gemini-3.5-flash-lite", "system instruction")
    mock_client = MagicMock()
    mock_file = MagicMock()
    mock_file.name = "files/test_file_id_999"

    sess.client = mock_client
    sess.uploaded_file = mock_file
    sess.is_initialized = True

    sess.close()

    mock_client.files.delete.assert_called_once_with(name="files/test_file_id_999")
    assert sess.uploaded_file is None
    assert not sess.is_initialized


def test_session_manager_eviction_closes_stale_sessions():
    """Verify BookSessionManager._evict_stale_sessions calls close() on evicted sessions."""
    from app.services.session_manager import BookSessionManager

    mgr = BookSessionManager(max_sessions=2, ttl_seconds=10)
    s1 = MagicMock()
    s1.last_accessed = 100
    s1.is_expired.return_value = False

    s2 = MagicMock()
    s2.last_accessed = 200
    s2.is_expired.return_value = False

    s3 = MagicMock()
    s3.last_accessed = 300
    s3.is_expired.return_value = False

    mgr._sessions = {"h1": s1, "h2": s2, "h3": s3}
    mgr._evict_stale_sessions()

    # LRU eviction: capacity is 2, so s1 (oldest accessed: 100) must be evicted and closed
    assert "h1" not in mgr._sessions
    s1.close.assert_called_once()


# ---------------------------------------------------------------------------
# 7. OCR Streaming and Fallback Ceiling
# ---------------------------------------------------------------------------


def test_extract_text_ocr_fallback_page_cap():
    """Verify extract_text_from_pdf enforces 30-page ceiling on fallback OCR."""

    # Verify that in app/pdf.py, max_allowed_ocr is set to 30
    pdf_py_path = os.path.join(PROJECT_ROOT, "app", "pdf.py")
    with open(pdf_py_path, encoding="utf-8") as f:
        content = f.read()

    assert "max_allowed_ocr = 30" in content
    assert "for page_idx in range(1, limit_ocr + 1):" in content
    assert "first_page=page_idx, last_page=page_idx" in content


# ---------------------------------------------------------------------------
# 8. Gitignore Protection
# ---------------------------------------------------------------------------


def test_gitignore_contains_session_rule():
    """Verify .gitignore includes *.session to prevent accidental commits."""
    gi_path = os.path.join(PROJECT_ROOT, ".gitignore")
    with open(gi_path, encoding="utf-8") as f:
        lines = [line.strip() for line in f]

    assert "*.session" in lines
    assert "*.session-journal" in lines


# ---------------------------------------------------------------------------
# 9. Text Cache & Sync Exclusion Guardrails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_library_ignores_text_cache_and_derivatives(
    async_client, temp_db_conn, test_data_dir
):
    """Verify that sync_library ignores .full.txt, .pdf.txt, and derivative cache files."""
    from unittest.mock import patch

    sync_dir = os.path.join(test_data_dir, "sync_exclusion_isolated")
    os.makedirs(sync_dir, exist_ok=True)

    # Create dummy files: a legitimate PDF and several cache files
    legit_pdf = os.path.join(sync_dir, "legit_book.pdf")
    with open(legit_pdf, "wb") as f:
        f.write(b"%PDF-1.4 legit book content")

    cache_full_txt = os.path.join(sync_dir, "legit_book.pdf.full.txt")
    with open(cache_full_txt, "w", encoding="utf-8") as f:
        f.write("Cached text content")

    cache_pdf_txt = os.path.join(sync_dir, "legit_book.pdf.txt")
    with open(cache_pdf_txt, "w", encoding="utf-8") as f:
        f.write("Cached text content")

    derivative_txt = os.path.join(sync_dir, "legit_book.txt")
    with open(derivative_txt, "w", encoding="utf-8") as f:
        f.write("Derivative text content")

    with (
        patch("app.routers.books.LIBRARY_ROOT", sync_dir),
        patch("app.routers.books.is_real_api_key", return_value=True),
    ):
        resp = await async_client.post(
            "/api/books/sync",
            headers={"X-AI-Provider": "gemini", "X-AI-Key": f"AIzaSy{'FakeKey' * 3}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Only the legitimate PDF should be enqueued, none of the cache files
        assert data["enqueued_count"] == 1


# ---------------------------------------------------------------------------
# 10. Gemini Rate Limiter Safety Guardrails (RPM and TPM)
# ---------------------------------------------------------------------------


def test_gemini_rate_limiter_defaults_and_sliding_window():
    """Verify GeminiRateLimiter respects configured RPM/TPM ceilings and handles sliding windows."""
    import time
    from unittest.mock import patch

    from app.tasks import GeminiRateLimiter

    limiter = GeminiRateLimiter()
    assert limiter.rpm == 13
    assert limiter.tpm == 210000

    # Under threshold - no sleep called
    with patch("time.sleep") as mock_sleep:
        limiter.wait_if_needed(estimated_tokens=50000)
        mock_sleep.assert_not_called()
        assert len(limiter.request_history) == 1
        assert limiter.request_times == [limiter.request_history[0][0]]

    # Exceeding TPM limit triggers sleep
    test_limiter = GeminiRateLimiter(rpm=5, tpm=1000)
    now = time.time()
    test_limiter.request_history = [(now - 10, 800)]
    with patch("time.sleep") as mock_sleep:

        def fake_sleep(seconds):
            test_limiter.request_history = []

        mock_sleep.side_effect = fake_sleep
        test_limiter.wait_if_needed(estimated_tokens=300)
        mock_sleep.assert_called_once()
