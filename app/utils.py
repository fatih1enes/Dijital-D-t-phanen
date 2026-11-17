"""Utility functions for Dijital Kütüphane."""

import hashlib
import os
import re
import unicodedata
import uuid
from pathlib import Path

from fastapi import HTTPException

DEFAULT_CATEGORY = "Genel"
DOC_EXT_PDF = ".pdf"
MASKED_LITERAL = "AIzaSy[MASKED]"
MASKED_PARAM_REPLACEMENT = r"\1[MASKED]"

_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)


def tr_lower(text: str | None) -> str:
    """Locale-accurate Turkish lowercase conversion (NFC normalized)."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFC", str(text))
    return norm.replace("İ", "i").replace("I", "ı").lower()


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
    norm = unicodedata.normalize("NFC", str(name))
    clean = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " - ", norm)
    clean = re.sub(r"\s+", " ", clean).strip(" .")
    if not clean or clean.upper().split(".")[0] in _WINDOWS_RESERVED_NAMES:
        return DEFAULT_CATEGORY
    return clean


def _clean_stem(raw_stem: str, max_len: int = 170, fallback_prefix: str = "dosya") -> str:
    """Normalize and sanitize a filename stem while preserving Unicode/Turkish letters."""
    norm = unicodedata.normalize("NFC", raw_stem or "")
    norm = norm.replace("—", "-").replace("–", "-")
    safe = re.sub(r"[^\w.\-\s()]+", "_", norm, flags=re.UNICODE)
    safe = re.sub(r"\.{2,}", "_", safe)
    safe = re.sub(r"\s+", " ", safe).strip(" ._")
    if safe.upper().split(".")[0] in _WINDOWS_RESERVED_NAMES:
        safe = f"_{safe}"
    if not safe:
        safe = f"{fallback_prefix}_{uuid.uuid4().hex[:12]}"
    return safe[:max_len].rstrip(" .")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage preserving Unicode letters and supported extensions."""
    normalized = unicodedata.normalize("NFC", filename or "").replace("\\", "/")
    raw = os.path.basename(normalized)
    if not raw:
        return f"dosya_{uuid.uuid4().hex}{DOC_EXT_PDF}"
    name, ext = os.path.splitext(raw)
    ext_lower = ext.lower()
    if ext_lower not in (DOC_EXT_PDF, ".epub", ".txt"):
        ext_lower = DOC_EXT_PDF
    safe_name = _clean_stem(name, max_len=170, fallback_prefix="dosya")
    return f"{safe_name}{ext_lower}"


def sanitize_export_stem(name: str | None, default: str = "kitap") -> str:
    """Produce a clean filename stem without document extension for export downloads (.md, .bib, .json)."""
    raw = unicodedata.normalize("NFC", str(name or "")).replace("\\", "/")
    base = os.path.basename(raw).strip()
    stem, ext = os.path.splitext(base)
    if ext.lower() in (DOC_EXT_PDF, ".epub", ".txt", ".md", ".json", ".bib", ".tsv"):
        base = stem
    return _clean_stem(base or default, max_len=150, fallback_prefix=default)


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
    """Check if content looks like an EPUB archive (PK zip signature, rejecting OOXML Office docs)."""
    if len(content) <= 4 or content[:4] != b"PK\x03\x04":
        return False
    probe = content[:512]
    if b"[Content_Types].xml" in probe:
        return False
    return True


def looks_like_txt(content: bytes) -> bool:
    """Check if content looks like plain text (non-empty and free of binary null bytes)."""
    if not content:
        return False
    return b"\x00" not in content[:2048]


def looks_like_supported_document(content: bytes, filename: str) -> tuple[bool, str]:
    """Check if document is supported (PDF, EPUB, TXT) and return (is_valid, doc_type)."""
    lower = (filename or "").lower()
    if lower.endswith(".pdf") or looks_like_pdf(content):
        return looks_like_pdf(content), "pdf"
    if lower.endswith(".epub") or looks_like_epub(content):
        return looks_like_epub(content), "epub"
    if lower.endswith(".txt"):
        return looks_like_txt(content), "txt"
    return False, "unknown"


def is_path_within(base_dir: str | os.PathLike[str], candidate_path: str | os.PathLike[str]) -> bool:
    """Check if candidate path is within base directory, safe against Windows drive casing and traversal attacks."""
    try:
        base = Path(base_dir).resolve(strict=False)
        candidate = Path(candidate_path).resolve(strict=False)
        if os.name == "nt":
            base = Path(os.path.normcase(str(base)))
            candidate = Path(os.path.normcase(str(candidate)))
        return candidate.is_relative_to(base)
    except (ValueError, OSError, RuntimeError):
        return False


def resolve_portable_book_path(stored_path: str | None, library_root: str) -> str:
    """Re-anchor a stored Dijital_Kutuphane path onto the active LIBRARY_ROOT if the project folder was moved/copied."""
    raw = str(stored_path or "").strip()
    if not raw:
        return ""
    norm_slashes = raw.replace("\\", "/")
    if ".." in norm_slashes.split("/"):
        return ""
    if is_path_within(library_root, raw) and os.path.exists(raw):
        return raw

    marker = "/Dijital_Kutuphane/"
    idx = norm_slashes.rfind(marker)
    if idx != -1:
        rel_part = norm_slashes[idx + len(marker) :].lstrip("/")
        if rel_part and ".." not in rel_part.split("/"):
            candidate = os.path.join(library_root, *rel_part.split("/"))
            if is_path_within(library_root, candidate) and os.path.exists(candidate):
                return candidate
    return raw


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
