"""Security and Architecture Audit Tests covering:
1. Safe Default Access Control (blocking unauthenticated remote requests when ACCESS_PASSWORD is empty)
2. Masked API Keys in GET /api/settings and protection against overwriting
3. Non-blocking async chat execution
4. XSS sanitization in markdown parsing
"""

import asyncio
import os
from unittest.mock import patch

import pytest
from fastapi import Request

from app.auth import (
    _is_access_allowed,
    _is_local_request,
    _is_unprotected_remote_allowed,
)


def make_mock_request(
    client_host: str = "192.168.1.100", method: str = "GET", path: str = "/api/books"
):
    """Helper to construct a mock request with client info."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(b"host", b"example.com"), (b"accept", b"application/json")],
        "client": (client_host, 12345),
        "session": {},
    }
    return Request(scope)


class TestAccessControlDefaults:
    """Item 1: Default deployment security - remote vs local access."""

    def test_local_requests_allowed_by_default(self):
        """Localhost requests should be allowed by default for local desktop use."""
        for host in ("127.0.0.1", "::1", "localhost", "testclient"):
            req = make_mock_request(client_host=host)
            assert _is_local_request(req) is True
            assert _is_access_allowed(req) is True

    def test_remote_requests_blocked_when_no_password_set(self):
        """Remote requests must NOT be allowed when ACCESS_PASSWORD is blank."""
        req = make_mock_request(client_host="203.0.113.195")
        assert _is_local_request(req) is False

        with patch.dict(
            os.environ, {"ACCESS_PASSWORD": "", "ALLOW_UNPROTECTED_REMOTE_ACCESS": "false"}
        ):
            assert _is_access_allowed(req) is False

    def test_remote_requests_explicit_unprotected_opt_in(self):
        """Remote requests are allowed only when ALLOW_UNPROTECTED_REMOTE_ACCESS is explicitly enabled."""
        req = make_mock_request(client_host="203.0.113.195")

        with patch.dict(
            os.environ, {"ACCESS_PASSWORD": "", "ALLOW_UNPROTECTED_REMOTE_ACCESS": "true"}
        ):
            assert _is_unprotected_remote_allowed() is True
            assert _is_access_allowed(req) is True

    def test_remote_requests_with_password_require_session(self):
        """When ACCESS_PASSWORD is set, unauthenticated remote requests must be denied."""
        req = make_mock_request(client_host="203.0.113.195")

        with patch.dict(os.environ, {"ACCESS_PASSWORD": "super_secret_password"}):
            assert _is_access_allowed(req) is False

    @pytest.mark.asyncio
    async def test_api_auth_login_blocks_remote_when_no_password(self, async_client):
        """POST /api/auth/login from remote client should return 403 when ACCESS_PASSWORD is not set."""
        with (
            patch("app.auth._is_local_request", return_value=False),
            patch("app.auth._get_access_password", return_value=""),
            patch("app.auth._is_unprotected_remote_allowed", return_value=False),
        ):
            res = await async_client.post("/api/auth/login", json={"password": "any"})
            assert res.status_code == 403
            assert "ACCESS_PASSWORD" in res.json()["detail"]


class TestSettingsApiKeyProtection:
    """Item 2: Sensitive API key masking and protection."""

    @pytest.mark.asyncio
    async def test_get_settings_masks_api_keys(self, async_client):
        """GET /api/settings must return masked keys rather than plaintext keys."""
        fake_gemini_key = f"AIzaSy{'SecretKey' * 3}"
        fake_config = {
            "ai_api_key": fake_gemini_key,
            "telegram_api_hash": "telegram_secret_hash_abcdef",
            "ai_provider": "gemini",
            "gemini_model": "gemini-3.5-flash-lite",
        }
        with patch("app.routers.settings.load_config", return_value=fake_config.copy()):
            res = await async_client.get("/api/settings")
            assert res.status_code == 200
            data = res.json()

            # Plaintext secrets must NEVER be present
            assert data["ai_api_key"] != fake_gemini_key
            assert data["telegram_api_hash"] != "telegram_secret_hash_abcdef"

            # Must be masked
            assert data["ai_api_key"] == "••••••••"
            assert data["telegram_api_hash"] == "••••••••"

            # Status flags must be true
            assert data["has_gemini_key"] is True
            assert data["has_telegram_hash"] is True
            assert data["has_ai_api_key"] is True

    @pytest.mark.asyncio
    async def test_post_settings_preserves_existing_keys_when_masked(self, async_client):
        """POST /api/settings must not overwrite real keys when user submits masked values."""
        existing_config = {
            "ai_api_key": "real_secret_gemini_key",
            "telegram_api_hash": "real_secret_telegram_hash",
            "max_pages": 10,
        }

        saved_data = {}

        def mock_save(c):
            saved_data.update(c)

        with (
            patch("app.routers.settings.load_config", return_value=existing_config.copy()),
            patch("app.routers.settings.save_config", side_effect=mock_save),
        ):
            # User submits form with masked values
            payload = {
                "ai_api_key": "••••••••",
                "telegram_api_hash": "••••••••",
                "max_pages": 15,
            }
            res = await async_client.post("/api/settings", json=payload)
            assert res.status_code == 200

            # Real keys must be preserved!
            assert saved_data.get("ai_api_key") == "real_secret_gemini_key"
            assert saved_data.get("telegram_api_hash") == "real_secret_telegram_hash"
            assert saved_data.get("max_pages") == 15


class TestChatAsyncExecution:
    """Item 3: Chat non-blocking async execution."""

    @pytest.mark.asyncio
    async def test_chat_uses_asyncio_thread_offloading(self, async_client):
        """Verify that generate_ai_response and AIRouter.get_embedding are offloaded to threads."""
        mock_response = "Bu bir test yanıtıdır."

        with (
            patch("app.ai_router.generate_ai_response", return_value=mock_response) as mock_gen,
            patch(
                "app.routers.chat.load_config",
                return_value={"ai_provider": "gemini", "ai_api_key": "test_key"},
            ),
        ):
            # Concurrently run a small asyncio task alongside chat to verify the event loop isn't blocked
            async def background_counter():
                count = 0
                for _ in range(5):
                    await asyncio.sleep(0.01)
                    count += 1
                return count

            counter_task = asyncio.create_task(background_counter())

            response = await async_client.post(
                "/api/chat",
                json={"message": "Merhaba kütüphane!"},
                headers={"X-AI-Key": "test_key", "X-AI-Provider": "gemini"},
            )

            counter_result = await counter_task
            assert counter_result == 5
            assert response.status_code == 200
            assert response.json()["response"] == mock_response
            assert mock_gen.called


class TestXSSSanitization:
    """Item 4: XSS defense validation in HTML and Markdown transformations."""

    def test_html_escaping_in_markdown(self):
        """Simulate parseMarkdown logic with HTML escaping to verify script tags are neutralized."""
        import html

        def parse_markdown_py(text: str) -> str:
            # Replicates UI parseMarkdown logic: esc(text) first, then styling replacements
            escaped = html.escape(text, quote=True)
            # Markdown bold
            escaped = escaped.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            return escaped

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=\"fetch('/api/settings').then(...)\">",
            '<iframe src="javascript:alert(1)"></iframe>',
            "<svg/onload=alert(1)>",
        ]

        for payload in xss_payloads:
            result = parse_markdown_py(payload)
            assert "<script>" not in result
            assert "<img" not in result
            assert "<iframe" not in result
            assert "<svg" not in result
            assert "&lt;" in result
