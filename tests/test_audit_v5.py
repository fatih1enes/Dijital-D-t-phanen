"""Comprehensive tests for Audit V5 security, reliability, and code quality improvements."""

import os
from unittest.mock import patch

import pytest

from app.auth import _is_allowed_origin
from app.config import load_config, save_config
from app.constants import (
    CHAT_CONTEXT_MAX_CHARS,
    DEFAULT_MAX_PAGES,
    MAX_CONCURRENT_TASKS,
    MAX_NATIVE_PDF_BYTES,
)
from app.task_queue import TaskQueue, extract_and_parse_json
from app.utils import is_path_within, mask_sensitive_data


class TestSecurityAuditV5:
    """Test suite covering critical security and stability audit items."""

    def test_session_secret_persistence(self, tmp_path):
        """Test that SESSION_SECRET is persisted to file when env variable is not set."""
        from app.constants import _get_or_create_session_secret

        with patch.dict(os.environ, {"SESSION_SECRET": ""}, clear=False):
            with patch("app.constants.DATA_DIR", str(tmp_path)):
                secret1 = _get_or_create_session_secret()
                assert len(secret1) >= 32
                # Second call should read the exact same secret from the file
                secret2 = _get_or_create_session_secret()
                assert secret1 == secret2

    def test_empty_origin_rejected(self):
        """Origin validation must return False for empty or whitespace origins."""
        assert _is_allowed_origin("") is False
        assert _is_allowed_origin("   ") is False
        assert _is_allowed_origin(None) is False
        assert _is_allowed_origin("http://malicious.com") is False
        assert _is_allowed_origin("http://localhost:8000") is True
        assert _is_allowed_origin("http://127.0.0.1:8000") is True

    def test_mask_sensitive_data(self):
        """Sensitive data masker must sanitize Gemini API keys, query keys, and tokens."""
        fake_key = f"AIzaSy{'dummy' * 7}"
        raw_msg = (
            f"Error connecting to https://generativelanguage.googleapis.com/v1beta/models?key={fake_key} "
            f"with api_key: '{fake_key}' and Bearer {'eyJhbGciOiJIUzI1NiI' + 'sInR5cCI6IkpXVCJ9'}"
        )
        masked = mask_sensitive_data(raw_msg)
        assert fake_key not in masked
        assert "[MASKED]" in masked

    def test_path_within_windows_case_and_traversal(self, tmp_path):
        """is_path_within must be robust against case differences and path traversal."""
        base = str(tmp_path / "library")
        os.makedirs(base, exist_ok=True)

        valid_file = os.path.join(base, "kategori", "book.pdf")
        os.makedirs(os.path.dirname(valid_file), exist_ok=True)
        with open(valid_file, "w") as f:
            f.write("test")

        # Normal child path
        assert is_path_within(base, valid_file) is True

        # Traversal attempt
        traversal = os.path.join(base, "..", "secret.txt")
        assert is_path_within(base, traversal) is False

        # Windows case variation simulation
        if os.name == "nt":
            upper_base = base.upper()
            lower_file = valid_file.lower()
            assert is_path_within(upper_base, lower_file) is True

    @pytest.mark.asyncio
    async def test_sql_injection_safe_distinct_values(self, temp_db):
        """get_distinct_values must only execute predefined queries and reject unwhitelisted columns."""
        # Whitelisted columns
        res_cat = await temp_db.get_distinct_values("kategori")
        assert isinstance(res_cat, list)
        res_author = await temp_db.get_distinct_values("yazar")
        assert isinstance(res_author, list)

        # Unwhitelisted / SQL injection attempt
        res_inject = await temp_db.get_distinct_values("kitap_adi; DROP TABLE kitaplar;--")
        assert res_inject == []

    def test_robust_json_parsing(self):
        """extract_and_parse_json must safely extract JSON from markdown and preserve internal newlines."""
        # Markdown fence with internal newlines inside summary
        raw_ai = """Here is the book analysis:
```json
{
    "kitap_adi": "Suç ve Ceza",
    "yazar": "Dostoyevski",
    "kategori": "Edebiyat",
    "alt_kategori": "Klasikler",
    "ozet": "Raskolnikov bir tefeci kadını öldürür.\\nVicdan azabı çeker.",
    "anahtar_kelimeler": "rus edebiyatı, felsefe",
}
```
Hope this helps!"""
        parsed = extract_and_parse_json(raw_ai)
        assert parsed["kitap_adi"] == "Suç ve Ceza"
        assert parsed["yazar"] == "Dostoyevski"
        assert "\n" in parsed["ozet"] or "\\n" in parsed["ozet"]

    def test_config_caching_and_invalidation(self, tmp_path):
        """load_config must cache results and re-read after save_config."""
        test_cfg_path = str(tmp_path / "config.json")
        with patch("app.config.CONFIG_PATH", test_cfg_path):
            # Save initial config
            initial = {"ai_provider": "gemini", "max_pages": 25}
            save_config(initial)

            cfg1 = load_config()
            assert cfg1["max_pages"] == 25

            # Save updated config
            save_config({"ai_provider": "ollama", "max_pages": 40})
            cfg2 = load_config()
            assert cfg2["max_pages"] == 40
            assert cfg2["ai_provider"] == "ollama"

    @pytest.mark.asyncio
    async def test_health_and_ready_endpoints(self, async_client):
        """Liveness (/health) and readiness (/ready) endpoints must respond with HTTP 200."""
        # /health
        resp_health = await async_client.get("/health")
        assert resp_health.status_code == 200
        data_h = resp_health.json()
        assert data_h["status"] == "ok"
        assert "timestamp" in data_h

        # /ready
        resp_ready = await async_client.get("/ready")
        assert resp_ready.status_code == 200
        data_r = resp_ready.json()
        assert data_r["status"] == "ready"
        assert data_r["database"] == "connected"

    def test_constants_defined(self):
        """Ensure critical constants are properly exported."""
        assert DEFAULT_MAX_PAGES == 20
        assert CHAT_CONTEXT_MAX_CHARS == 750000
        assert MAX_NATIVE_PDF_BYTES == 200 * 1024 * 1024
        assert MAX_CONCURRENT_TASKS >= 1

    def test_task_queue_configurable_and_graceful_shutdown(self):
        """TaskQueue must respect max_workers and shut down gracefully."""
        tq = TaskQueue(max_workers=3)
        assert tq._executor._max_workers == 3
        tq.shutdown(wait=True)
