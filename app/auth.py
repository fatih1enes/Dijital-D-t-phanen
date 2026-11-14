"""Authentication and authorization functions."""

import ipaddress
import os
import secrets
import threading
import time
import uuid
from typing import Any

from fastapi import HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse

from app.constants import (
    ALLOWED_ORIGINS as DEFAULT_ALLOWED_ORIGINS,
)
from app.constants import (
    AUTH_COOKIE_NAME,
    COOKIE_SECURE,
    LOGIN_LOCK_SECONDS,
    LOGIN_MAX_ATTEMPTS,
    LOGIN_WINDOW_SECONDS,
)

# Global auth state
_auth_lock = threading.Lock()
_TOKEN_TTL = 60 * 60 * 24 * 7  # 7 days
AUTH_STATE: dict[str, Any] = {
    "boot_id": uuid.uuid4().hex,
    "valid_tokens": {},  # token -> expiry_timestamp
    "attempts": {},
}

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "").strip()
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "").strip()
ALLOW_UNPROTECTED_REMOTE_ACCESS = os.environ.get(
    "ALLOW_UNPROTECTED_REMOTE_ACCESS", ""
).strip().lower() in ("true", "1", "yes")


def _get_access_password() -> str:
    """Get active access password from env, config or module variable."""
    env_pwd = os.environ.get("ACCESS_PASSWORD", "").strip()
    if env_pwd:
        return env_pwd
    try:
        from app.config import load_config

        cfg = load_config()
        cfg_pwd = str(cfg.get("access_password") or "").strip()
        if cfg_pwd:
            return cfg_pwd
    except Exception as e:
        import logging

        logging.debug("Could not read access_password from config: %s", e)
    return ACCESS_PASSWORD.strip()


def _is_unprotected_remote_allowed() -> bool:
    """Check if unprotected remote access is explicitly permitted."""
    return os.environ.get("ALLOW_UNPROTECTED_REMOTE_ACCESS", "").strip().lower() in (
        "true",
        "1",
        "yes",
    )


def _is_local_host(host: str | None) -> bool:
    """Check if host is localhost."""
    return (host or "") in ("127.0.0.1", "::1", "localhost", "testclient")


def _is_local_request(request: Request) -> bool:
    """Check if request physically originates from localhost socket, immune to header spoofing."""
    if not request.client or not request.client.host:
        return False
    if not _is_local_host(request.client.host):
        return False
    trust_proxy = os.environ.get("TRUST_PROXY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first_hop = forwarded.split(",")[0].strip()
            return _is_local_host(first_hop)
    return True


def _get_boot_id() -> str:
    """Get current boot ID."""
    with _auth_lock:
        return str(AUTH_STATE.get("boot_id") or "")


def _get_client_host(request: Request) -> str:
    """Get client host from request, extracting X-Forwarded-For only when TRUST_PROXY is enabled and request is from trusted proxy."""
    if not request.client or not request.client.host:
        return "unknown"
    trust_proxy = os.environ.get("TRUST_PROXY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if trust_proxy and _is_local_host(request.client.host):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return str(request.client.host)


def _prune_attempts(times: list[float], now_ts: float) -> list[float]:
    """Prune old login attempts."""
    return [t for t in times if now_ts - t <= LOGIN_WINDOW_SECONDS]


def _is_login_locked(client_host: str, now_ts: float) -> bool:
    """Check if login is locked for client."""
    with _auth_lock:
        state = AUTH_STATE["attempts"].get(client_host)
        if not state:
            return False
        lock_until = float(state.get("lock_until") or 0)
        return now_ts < lock_until


def _register_login_failure(client_host: str, now_ts: float) -> None:
    """Register a failed login attempt."""
    with _auth_lock:
        state = AUTH_STATE["attempts"].setdefault(client_host, {"times": [], "lock_until": 0})
        times = _prune_attempts(state.get("times", []), now_ts)
        times.append(now_ts)
        state["times"] = times
        if len(times) >= LOGIN_MAX_ATTEMPTS:
            state["lock_until"] = now_ts + LOGIN_LOCK_SECONDS


def _clear_login_attempts(client_host: str) -> None:
    """Clear login attempts for client."""
    with _auth_lock:
        AUTH_STATE["attempts"].pop(client_host, None)


def _remaining_lock_seconds(client_host: str, now_ts: float) -> int:
    """Get remaining lock seconds."""
    with _auth_lock:
        state = AUTH_STATE["attempts"].get(client_host) or {}
        lock_until = float(state.get("lock_until") or 0)
        return max(0, int(lock_until - now_ts))


def _rotate_auth_boot_id() -> None:
    """Rotate auth boot ID."""
    with _auth_lock:
        AUTH_STATE["boot_id"] = uuid.uuid4().hex
        AUTH_STATE["valid_tokens"].clear()
        AUTH_STATE["attempts"].clear()


def _cleanup_expired_tokens() -> None:
    """Remove expired tokens."""
    with _auth_lock:
        now = time.time()
        expired = [t for t, exp in AUTH_STATE["valid_tokens"].items() if now > exp]
        for t in expired:
            AUTH_STATE["valid_tokens"].pop(t, None)


def _normalized_origin(origin: str) -> str:
    """Normalize origin string."""
    return str(origin or "").strip().rstrip("/").lower()


def _is_matching_host(normalized: str, host: str) -> bool:
    """Check if normalized origin matches host under standard web schemes without hardcoded cleartext URLs."""
    scheme, sep, netloc = normalized.partition("://")
    return bool(sep) and netloc == host.lower() and scheme in ("http", "https")


def _is_host_private_or_local(host_name: str) -> bool:
    """Determine if a given hostname is loopback, local, or private IP."""
    if _is_local_host(host_name) or host_name in ("0.0.0.0",):
        return True
    try:
        ip = ipaddress.ip_address(host_name)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def _extract_host_name(host: str) -> str:
    """Extract host name from Host header, stripping ports and IPv6 brackets."""
    if host.startswith("[") and "]" in host:
        return host[1 : host.index("]")]
    if ":" in host:
        return host.split(":")[0].strip()
    return host


def _is_allowed_origin(
    origin: str,
    request: Request | WebSocket | None = None,
    allowed_origins: Any = None,
    **kwargs: Any,
) -> bool:
    """Check if origin is allowed."""
    if allowed_origins is None:
        allowed_origins = kwargs.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    normalized = _normalized_origin(origin)
    if not normalized:
        return False

    if normalized in {_normalized_origin(item) for item in allowed_origins}:
        return True

    if request:
        host = request.headers.get("host")
        if host:
            host_name = _extract_host_name(host)
            if _is_host_private_or_local(host_name) and _is_matching_host(normalized, host):
                return True
    return False


def _ensure_safe_request_origin(
    request: Request, allowed_origins: Any = None, **kwargs: Any
) -> None:
    """Ensure request has safe origin."""
    if allowed_origins is None:
        allowed_origins = kwargs.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    origin = request.headers.get("Origin", "").strip()
    if origin:
        if not _is_allowed_origin(origin, request, allowed_origins):
            raise HTTPException(status_code=403, detail="Invalid origin")
        return

    # If Origin header is not present on state-changing requests, check Referer if available
    referer = request.headers.get("Referer", "").strip()
    if referer:
        from urllib.parse import urlparse

        ref_parsed = urlparse(referer)
        ref_origin = f"{ref_parsed.scheme}://{ref_parsed.netloc}"
        if not _is_allowed_origin(ref_origin, request, allowed_origins):
            raise HTTPException(status_code=403, detail="Invalid referer origin")


def _is_session_authenticated(request: Request) -> bool:
    """Check if session is authenticated."""
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token:
        with _auth_lock:
            if token in AUTH_STATE["valid_tokens"]:
                if time.time() <= AUTH_STATE["valid_tokens"][token]:
                    return True
                else:
                    AUTH_STATE["valid_tokens"].pop(token, None)
    try:
        boot_id = _get_boot_id()
        is_auth = bool(request.session.get("authenticated"))
        session_boot_id = str(request.session.get("boot_id") or "")
        return is_auth and secrets.compare_digest(session_boot_id, boot_id)
    except Exception:
        return False


def _is_access_allowed(request: Request) -> bool:
    """Check if access is allowed."""
    if _is_local_request(request):
        return True
    if _is_session_authenticated(request):
        return True
    password = _get_access_password()
    if not password:
        return _is_unprotected_remote_allowed()
    return False


def _ensure_authorized(
    request: Request,
    allow_local: bool = True,
    allowed_origins: Any = None,
    **kwargs: Any,
) -> None:
    """Ensure request is authorized."""
    if allowed_origins is None:
        allowed_origins = kwargs.get("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    _ensure_safe_request_origin(request, allowed_origins)
    if allow_local and _is_local_request(request):
        return
    if _is_session_authenticated(request):
        return
    admin_token = os.environ.get("ADMIN_TOKEN", ADMIN_TOKEN).strip()
    if admin_token:
        provided = request.headers.get("X-Admin-Token", "").strip()
        if provided and secrets.compare_digest(provided, admin_token):
            return
    raise HTTPException(status_code=403, detail="Unauthorized")


def _set_session_authenticated(request: Request, value: bool) -> None:
    """Set session authentication status."""
    try:
        request.session["authenticated"] = bool(value)
        request.session["boot_id"] = _get_boot_id() if value else ""
    except Exception as e:
        import logging

        logging.debug("Could not update request.session authentication state: %s", e)


def _auth_success_response() -> JSONResponse:
    """Return successful authentication response."""
    token = secrets.token_hex(32)
    _cleanup_expired_tokens()
    with _auth_lock:
        AUTH_STATE["valid_tokens"][token] = time.time() + _TOKEN_TTL

    resp = JSONResponse({"status": "ok"})
    resp.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
        max_age=60 * 60 * 24 * 7,
    )
    return resp
