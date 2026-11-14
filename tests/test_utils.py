import re

import pytest
from fastapi import HTTPException

from app.utils import (
    get_file_hash,
    get_file_hash_from_path,
    looks_like_pdf,
    sanitize_dirname,
    sanitize_filename,
    validate_file_hash,
)


class TestFileHash:
    """Test file hashing functionality."""

    def test_get_file_hash(self):
        """Test SHA256 hash generation."""
        test_data = b"test data for hashing"
        hash_result = get_file_hash(test_data)

        # Verify it's a valid SHA256 hash (64 hex characters)
        assert len(hash_result) == 64
        assert re.match(r"^[a-f0-9]{64}$", hash_result)

        # Verify consistency
        hash_result2 = get_file_hash(test_data)
        assert hash_result == hash_result2

    def test_get_file_hash_from_path(self, tmp_path):
        """Test streaming SHA256 hash generation from file path."""
        test_data = b"streamed test data" * 1000
        test_file = tmp_path / "sample.pdf"
        test_file.write_bytes(test_data)

        expected_hash = get_file_hash(test_data)
        streamed_hash = get_file_hash_from_path(str(test_file), chunk_size=128)

        assert streamed_hash == expected_hash

    def test_different_data_different_hash(self):
        """Test that different data produces different hashes."""
        hash1 = get_file_hash(b"data1")
        hash2 = get_file_hash(b"data2")
        assert hash1 != hash2


class TestSanitization:
    """Test filename and directory name sanitization."""

    def test_sanitize_dirname_basic(self):
        """Test basic directory name sanitization."""
        assert sanitize_dirname("Test Category") == "Test Category"
        assert sanitize_dirname("Test/Category") == "Test - Category"
        assert sanitize_dirname("Test:Category") == "Test - Category"

    def test_sanitize_dirname_special_chars(self):
        """Test special character removal."""
        assert sanitize_dirname('Test*?"<>|Category') == "Test - Category"
        assert sanitize_dirname("Test\\Category") == "Test - Category"

    def test_sanitize_dirname_empty(self):
        """Test empty string handling."""
        assert sanitize_dirname("") == "Genel"
        assert sanitize_dirname(None) == "Genel"

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("test.pdf") == "test.pdf"
        assert sanitize_filename("test file.pdf") == "test file.pdf"

    def test_sanitize_filename_special_chars(self):
        """Test special character removal in filenames."""
        result = sanitize_filename("test@#$file.pdf")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert result.endswith(".pdf")

    def test_sanitize_filename_no_extension(self):
        """Test adding PDF extension when missing."""
        result = sanitize_filename("testfile")
        assert result.endswith(".pdf")

    def test_sanitize_filename_long(self):
        """Test filename length limiting."""
        long_name = "a" * 200 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 180 + 4  # 180 chars + .pdf

    def test_validate_file_hash_valid(self):
        """Test valid hash validation."""
        valid_hash = "a" * 64
        assert validate_file_hash(valid_hash) == valid_hash

    def test_validate_file_hash_invalid(self):
        """Test invalid hash validation raises exception."""
        with pytest.raises(HTTPException):
            validate_file_hash("invalid")

        with pytest.raises(HTTPException):
            validate_file_hash("a" * 63)  # Too short


class TestPDFDetection:
    """Test PDF file detection."""

    def test_looks_like_pdf_valid(self):
        """Test valid PDF detection."""
        valid_pdf = b"%PDF-1.4\nsome content"
        assert looks_like_pdf(valid_pdf)

    def test_looks_like_pdf_invalid(self):
        """Test invalid PDF detection."""
        invalid_pdf = b"Not a PDF file"
        assert not looks_like_pdf(invalid_pdf)

    def test_looks_like_pdf_empty(self):
        """Test empty bytes handling."""
        assert not looks_like_pdf(b"")
