"""Utility functions for Dijital Kütüphane."""

import hashlib
import os
import re
import uuid

from fastapi import HTTPException

DEFAULT_CATEGORY = "Genel"
DOC_EXT_PDF = ".pdf"
MASKED_LITERAL = "AIzaSy[MASKED]"
MASKED_PARAM_REPLACEMENT = r"\1[MASKED]"


def get_file_hash(file_bytes: bytes) -> str:
    """Generate SHA256 hash of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def get_file_hash_from_path(filepath: str, chunk_size: int = 65536) -> str:
    """Generate SHA256 hash by streaming chunks directly from disk to avoid RAM exhaustion."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def sanitize_dirname(name: str | None) -> str:
    """Convert category strings into safe folder names for Windows."""
    if not name:
        return DEFAULT_CATEGORY
    clean = re.sub(r'[\\/:*?"<>|]+', " - ", str(name))
    clean = re.sub(r"\s+", " ", clean).strip(" .")
    return clean or DEFAULT_CATEGORY


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage preserving supported extensions."""
    normalized = (filename or "").replace("\\", "/")
    raw = os.path.basename(normalized)
    if not raw:
        return f"dosya_{uuid.uuid4().hex}{DOC_EXT_PDF}"
    name, ext = os.path.splitext(raw)
    ext_lower = ext.lower()
    if ext_lower not in (DOC_EXT_PDF, ".epub", ".txt"):
        ext_lower = DOC_EXT_PDF
    safe_name = re.sub(r"[^A-Za-z0-9._\-\s()]+", "_", name)
    safe_name = re.sub(r"\.{2,}", "_", safe_name).strip(" ._")
    if not safe_name:
        safe_name = f"dosya_{uuid.uuid4().hex}"
    return f"{safe_name[:170]}{ext_lower}"


def validate_file_hash(file_hash: str) -> str:
    """Validate file hash format."""
    candidate = str(file_hash or "").strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", candidate):
        raise HTTPException(status_code=400, detail="Invalid book ID")
    return candidate


def looks_like_pdf(content: bytes) -> bool:
    """Check if content looks like a PDF file."""
    return b"%PDF-" in content[:1024]


def looks_like_epub(content: bytes) -> bool:
    """Check if content looks like an EPUB (PK zip archive)."""
    return len(content) > 4 and content[:2] == b"PK"


def looks_like_supported_document(content: bytes, filename: str) -> tuple[bool, str]:
    """Check if document is supported (PDF, EPUB, TXT) and return (is_valid, doc_type)."""
    lower = filename.lower()
    if lower.endswith(".pdf") or looks_like_pdf(content):
        return looks_like_pdf(content), "pdf"
    if lower.endswith(".epub") or looks_like_epub(content):
        return looks_like_epub(content), "epub"
    if lower.endswith(".txt"):
        return True, "txt"
    return False, "unknown"


def is_path_within(base_dir: str, candidate_path: str) -> bool:
    """Check if candidate path is within base directory, safe against Windows drive casing and traversal attacks."""
    try:
        base = os.path.realpath(os.path.abspath(base_dir))
        candidate = os.path.realpath(os.path.abspath(candidate_path))
        if os.name == "nt":
            base = os.path.normcase(base)
            candidate = os.path.normcase(candidate)
        rel = os.path.relpath(candidate, base)
        return rel == "." or (not rel.startswith("..") and not os.path.isabs(rel))
    except (ValueError, OSError):
        return False


def mask_sensitive_data(text: str | None) -> str:
    """Mask API keys, tokens, and credentials in strings and error messages to prevent credential leakage."""
    if not text:
        return ""
    s = str(text)
    # Mask Gemini API keys
    s = re.sub(r"AIza[A-Za-z0-9_-]{35}", MASKED_LITERAL, s)
    # Mask key query params in URLs or exception text
    s = re.sub(r'([?&]key=)[^&\s"\']+', MASKED_PARAM_REPLACEMENT, s)
    # Mask api_key parameters in JSON/dict dumps (flags=re.IGNORECASE, so a-z covers both casing)
    s = re.sub(
        r'(api[-_]?key["\']?\s*[:=]\s*["\']?)[a-z0-9_-]{8,}',
        MASKED_PARAM_REPLACEMENT,
        s,
        flags=re.IGNORECASE,
    )
    # Mask Bearer tokens
    s = re.sub(
        r"(Bearer\s+)[a-z0-9_.-]{15,}",
        MASKED_PARAM_REPLACEMENT,
        s,
        flags=re.IGNORECASE,
    )
    return s
