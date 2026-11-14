import os
import secrets
import sys

from dotenv import load_dotenv

# Base directory resolution (handles standard Python execution & PyInstaller frozen bundles)
IS_FROZEN = getattr(sys, "frozen", False)
if IS_FROZEN:
    # Read-only bundled resources (static assets, templates) live in _MEIPASS or _internal
    BUNDLE_ROOT = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    # Mutable application directory (user's veriler folder, config.json, .env) lives next to executable
    APP_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__))))
    APP_DIR = BUNDLE_ROOT

PROJECT_ROOT = APP_DIR

_env_path = os.path.join(APP_DIR, ".env")
if os.path.exists(_env_path):
    load_dotenv(dotenv_path=_env_path, override=True)

STATIC_DIR = os.path.join(BUNDLE_ROOT, "static")
TEMPLATES_DIR = os.path.join(BUNDLE_ROOT, "templates")
DATA_DIR = os.path.join(APP_DIR, "veriler")
ARCHIVE_DIR = os.path.join(DATA_DIR, "Kaldirilmis_PDFler")
LIBRARY_ROOT = os.path.realpath(os.path.abspath(os.path.join(DATA_DIR, "Dijital_Kutuphane")))
THUMBNAILS_DIR = os.path.realpath(os.path.abspath(os.path.join(DATA_DIR, "thumbnails")))


def _safe_int_env(key: str, default: int) -> int:
    val = os.environ.get(key, "").strip()
    if not val:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# File size limits
MAX_UPLOAD_BYTES = _safe_int_env("MAX_UPLOAD_MB", 250) * 1024 * 1024
MAX_COVER_BYTES = _safe_int_env("MAX_COVER_MB", 8) * 1024 * 1024
MAX_IMAGE_PIXELS = _safe_int_env("MAX_IMAGE_PIXELS", 25000000)
CHUNK_READ_SIZE = 1024 * 1024

# AI constants
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"

# Task Queue & Worker Limits
MAX_CONCURRENT_TASKS = max(1, _safe_int_env("MAX_CONCURRENT_TASKS", 1))

# Processing & Chat Limits
DEFAULT_MAX_PAGES = 20
CHAT_CONTEXT_MAX_CHARS = 750000
MAX_NATIVE_PDF_BYTES = 200 * 1024 * 1024
OCR_TRIGGER_MIN_CHARS = 200

# Authentication constants
AUTH_COOKIE_NAME = "library_auth"


def _get_or_create_session_secret() -> str:
    """Resolve session secret from env or persist a generated secret in DATA_DIR across restarts."""
    import logging

    raw = os.environ.get("SESSION_SECRET", "").strip()
    if raw and raw != "change-this-in-production":
        return raw
    secret_file = os.path.join(DATA_DIR, ".session_secret")
    if os.path.exists(secret_file):
        try:
            with open(secret_file, encoding="utf-8") as f:
                saved = f.read().strip()
                if saved:
                    return saved
        except Exception as e:
            logging.debug("Could not read .session_secret: %s", e)
    new_secret = secrets.token_hex(32)
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write(new_secret)
        if hasattr(os, "chmod"):
            try:
                os.chmod(secret_file, 0o600)
            except OSError as e:
                logging.debug("Could not chmod .session_secret: %s", e)
    except Exception as e:
        logging.debug("Could not write .session_secret: %s", e)
    return new_secret


SESSION_SECRET = _get_or_create_session_secret()
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0").strip() == "1"
LOGIN_WINDOW_SECONDS = _safe_int_env("LOGIN_WINDOW_SECONDS", 300)
LOGIN_MAX_ATTEMPTS = _safe_int_env("LOGIN_MAX_ATTEMPTS", 5)
LOGIN_LOCK_SECONDS = _safe_int_env("LOGIN_LOCK_SECONDS", 600)

# Allowed Origins for CORS and Origin validation
_default_origins = "http://127.0.0.1:8000,http://localhost:8000,http://[::1]:8000"
_raw_origins = os.environ.get("ALLOWED_ORIGINS", _default_origins)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# Standard categories
STANDARD_CATEGORIES = [
    "Edebiyat ve Kurgu",
    "Bilim ve Teknoloji",
    "Siyaset Bilimi",
    "Tarih ve Arkeoloji",
    "Felsefe",
    "Sosyoloji ve Antropoloji",
    "Psikoloji",
    "Hukuk",
    "Ekonomi",
    "Din ve İlahiyat",
    "Sanat ve Mimari",
    "Biyografi ve Anı",
    "Kişisel Gelişim",
    "Coğrafya ve Gezi",
    "Eğitim",
    "Araştırma, İnceleme ve Eleştiri",
]

# Logging
MAX_LOGS = 1000

# Create directories
os.makedirs(LIBRARY_ROOT, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "logs"), exist_ok=True)
