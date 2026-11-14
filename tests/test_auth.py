import time
from unittest.mock import patch

import pytest

from app.auth import (
    AUTH_STATE,
    _clear_login_attempts,
    _is_local_host,
    _is_login_locked,
    _register_login_failure,
    _remaining_lock_seconds,
)


class TestLocalRequestDetection:
    """Test local request detection."""

    def test_is_local_host_localhost(self):
        """Test localhost detection."""
        assert _is_local_host("localhost")
        assert _is_local_host("127.0.0.1")
        assert _is_local_host("::1")

    def test_is_local_host_remote(self):
        """Test remote host detection."""
        assert not _is_local_host("192.168.1.1")
        assert not _is_local_host("8.8.8.8")
        assert not _is_local_host("")

    def test_is_local_host_none(self):
        """Test None handling."""
        assert not _is_local_host(None)


class TestLoginAttemptTracking:
    """Test login attempt tracking and rate limiting."""

    def setup_method(self):
        """Clear attempt state before each test."""
        AUTH_STATE["attempts"].clear()

    def test_register_login_failure(self):
        """Test registering failed login attempts."""
        client_host = "192.168.1.1"
        _register_login_failure(client_host, time.time())

        assert client_host in AUTH_STATE["attempts"]
        assert len(AUTH_STATE["attempts"][client_host]["times"]) == 1

    def test_multiple_login_failures(self):
        """Test multiple failed login attempts."""
        client_host = "192.168.1.1"
        now = time.time()

        for _ in range(3):
            _register_login_failure(client_host, now)

        assert len(AUTH_STATE["attempts"][client_host]["times"]) == 3

    def test_login_lock_after_max_attempts(self):
        """Test that account locks after max attempts."""
        client_host = "192.168.1.1"
        now = time.time()

        # Register max attempts
        for _ in range(5):
            _register_login_failure(client_host, now)

        # Should be locked
        assert _is_login_locked(client_host, now)

    def test_login_not_locked_before_max_attempts(self):
        """Test that account is not locked before max attempts."""
        client_host = "192.168.1.1"
        now = time.time()

        # Register less than max attempts
        for _ in range(3):
            _register_login_failure(client_host, now)

        # Should not be locked
        assert not _is_login_locked(client_host, now)

    def test_lock_expires_after_timeout(self):
        """Test that lock expires after timeout period."""
        client_host = "192.168.1.1"
        now = time.time()

        # Register max attempts
        for _ in range(5):
            _register_login_failure(client_host, now)

        # Should be locked immediately
        assert _is_login_locked(client_host, now)

        # Should not be locked after timeout (600 seconds)
        future_time = now + 700
        assert not _is_login_locked(client_host, future_time)

    def test_clear_login_attempts(self):
        """Test clearing login attempts."""
        client_host = "192.168.1.1"
        now = time.time()

        _register_login_failure(client_host, now)
        assert client_host in AUTH_STATE["attempts"]

        _clear_login_attempts(client_host)
        assert client_host not in AUTH_STATE["attempts"]

    def test_remaining_lock_seconds(self):
        """Test remaining lock seconds calculation."""
        client_host = "192.168.1.1"
        now = time.time()

        # Register max attempts
        for _ in range(5):
            _register_login_failure(client_host, now)

        remaining = _remaining_lock_seconds(client_host, now)
        assert remaining > 0
        assert remaining <= 600  # Max lock seconds


class TestOriginValidation:
    """Test origin validation for CSRF protection."""

    def test_normalize_origin(self):
        """Test origin normalization."""
        from app.auth import _normalized_origin

        assert _normalized_origin("http://localhost:8000") == "http://localhost:8000"
        assert _normalized_origin("http://localhost:8000/") == "http://localhost:8000"
        assert _normalized_origin("  HTTP://LOCALHOST:8000  ") == "http://localhost:8000"


class TestLoginEndpointRateLimiting:
    """Test rate limiting and brute-force protection on /api/auth/login."""

    @pytest.mark.asyncio
    async def test_login_brute_force_lock(self, async_client):
        """Five failed attempts should trigger 429 lock."""
        from app.auth import _clear_login_attempts

        # Clean state for test client host
        _clear_login_attempts("testclient")

        with (
            patch("app.auth._get_access_password", return_value="SecretPass123!"),
            patch("app.auth._is_local_request", return_value=False),
        ):
            # 5 consecutive failed attempts
            for i in range(5):
                res = await async_client.post("/api/auth/login", json={"password": "WrongPassword"})
                assert res.status_code == 401, f"Attempt {i + 1} should return 401"

            # 6th attempt must be locked out with 429
            locked_res = await async_client.post(
                "/api/auth/login", json={"password": "SecretPass123!"}
            )
            assert locked_res.status_code == 429
            assert "Çok fazla" in locked_res.json()["detail"]

        _clear_login_attempts("testclient")
