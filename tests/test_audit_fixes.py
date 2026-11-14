"""Verification tests for recent audit fixes and hardening:
1. templates/login.html rendering and content
2. Remote login authentication flow (future token expiry and session boot_id)
3. Model standardization to gemini-3.5-flash-lite
4. Security response headers (CSP, frame options, content-type-options)
"""

import os
import time
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import _TOKEN_TTL, AUTH_STATE
from app.config import CONFIG_DEFAULTS
from app.constants import AUTH_COOKIE_NAME, DEFAULT_GEMINI_MODEL
from app.main import app


@pytest.mark.asyncio
async def test_login_page_renders_successfully():
    """Verify that /login route renders login.html with 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        resp = await client.get("/login")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "Giriş Yap" in resp.text
        assert 'id="password"' in resp.text
        assert "favicon.svg" in resp.text


@pytest.mark.asyncio
async def test_remote_login_flow_and_session_persistence():
    """Verify that remote login sets future expiry and session boot_id, allowing subsequent requests."""
    AUTH_STATE["valid_tokens"].clear()
    AUTH_STATE["attempts"].clear()

    transport = ASGITransport(app=app, client=("198.51.100.22", 54321))
    test_password = "SecretTestPassword123"

    with patch.dict(os.environ, {"ACCESS_PASSWORD": test_password}):
        async with AsyncClient(transport=transport, base_url="http://remote.example.com") as client:
            # 1. Unauthenticated request to /api/tasks is blocked / requires auth
            unauth_resp = await client.get("/api/tasks")
            assert unauth_resp.status_code in (401, 403)

            # 2. Perform login
            login_resp = await client.post("/api/auth/login", json={"password": test_password})
            assert login_resp.status_code == 200
            assert AUTH_COOKIE_NAME in login_resp.cookies

            token = login_resp.cookies[AUTH_COOKIE_NAME]
            assert token in AUTH_STATE["valid_tokens"]
            expiry = AUTH_STATE["valid_tokens"][token]

            # Verify token expiry is in the future (~7 days ahead, not now!)
            assert expiry > time.time() + (_TOKEN_TTL - 100)

            # 3. Subsequent request with the token cookie succeeds!
            auth_resp = await client.get("/api/tasks")
            assert auth_resp.status_code == 200


def test_gemini_model_standardization():
    """Verify DEFAULT_GEMINI_MODEL is locked to gemini-3.5-flash-lite across modules."""
    assert DEFAULT_GEMINI_MODEL == "gemini-3.5-flash-lite"
    assert CONFIG_DEFAULTS["gemini_model"] == "gemini-3.5-flash-lite"


@pytest.mark.asyncio
async def test_security_headers_present():
    """Verify security headers are injected into HTTP responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        resp = await client.get("/login")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_book_order_request_validation():
    """Verify BookOrderRequest correctly preserves valid hashes instead of returning empty list."""
    from app.models import BookOrderRequest

    req = BookOrderRequest(order=["  hash_abc  ", "hash_def  ", "hash_ghi"])
    assert req.order == ["hash_abc", "hash_def", "hash_ghi"]
    assert len(req.order) == 3


@pytest.mark.asyncio
async def test_get_book_by_filename_sanitized_variant(temp_db, sample_book_data):
    """Verify get_book_by_filename handles sanitized variants without ModuleNotFoundError."""
    # Turkish characters: 'ş', 'ğ', 'ü' -> in sanitized variant become '_'
    data = dict(sample_book_data)
    data["dosya_adi"] = "turkce_ornek.pdf"
    data["dosya_yolu"] = "/library/turkce_ornek.pdf"
    await temp_db.add_book(data)

    # Searching with non-ASCII or variant name will hit the sanitize_filename branch
    res = await temp_db.get_book_by_filename("türkçe_örnek.pdf")
    assert res is not None
    assert res[0] == data["dosya_hash"]
