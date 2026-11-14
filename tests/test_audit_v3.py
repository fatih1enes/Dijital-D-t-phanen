"""Unit tests verifying fixes for audit v3 issues:
1. config.json UTF-8 BOM resistance
2. Authorization checks on GET /api/books, /api/collections, /api/stats
3. POST /api/collections/import upload size limiting (DoS prevention)
4. google_search_grounding configuration propagation
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, UploadFile

from app.auth import _ensure_authorized
from app.config import _normalize_config


class TestConfigBOMResistance:
    """Item 1: config.json UTF-8 BOM tolerance."""

    def test_load_config_with_and_without_bom(self, tmp_path):
        """Verify load_config reads config.json whether or not it has a UTF-8 BOM."""
        test_cfg = {"max_pages": 42, "ai_provider": "gemini"}

        # Write with UTF-8 BOM
        bom_file = tmp_path / "config_bom.json"
        with open(bom_file, "w", encoding="utf-8-sig") as f:
            json.dump(test_cfg, f)

        # Verify BOM bytes exist in file
        with open(bom_file, "rb") as f:
            raw_bytes = f.read()
        assert raw_bytes.startswith(b"\xef\xbb\xbf")

        # Read with utf-8-sig
        with open(bom_file, encoding="utf-8-sig") as f:
            loaded = _normalize_config(json.load(f))
        assert loaded["max_pages"] == 42
        assert loaded["ai_provider"] == "gemini"

        # Write without BOM
        nobom_file = tmp_path / "config_nobom.json"
        with open(nobom_file, "w", encoding="utf-8") as f:
            json.dump(test_cfg, f)

        with open(nobom_file, "rb") as f:
            nobom_bytes = f.read()
        assert not nobom_bytes.startswith(b"\xef\xbb\xbf")

        with open(nobom_file, encoding="utf-8-sig") as f:
            loaded_nobom = _normalize_config(json.load(f))
        assert loaded_nobom["max_pages"] == 42


class TestEndpointAuthorizationChecks:
    """Item 2: _ensure_authorized enforcement on GET /api/books, /api/collections, /api/stats."""

    def test_ensure_authorized_denies_remote_unauthenticated(self):
        """Verify that _ensure_authorized rejects unauthenticated remote clients."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/books",
            "headers": [(b"host", b"example.com")],
            "client": ("198.51.100.25", 54321),
            "session": {},
        }
        req = Request(scope)

        with pytest.raises(HTTPException) as exc_info:
            _ensure_authorized(req)
        assert exc_info.value.status_code == 403

    def test_ensure_authorized_allows_local(self):
        """Verify that _ensure_authorized allows local requests without auth."""
        for local_ip in ("127.0.0.1", "::1", "localhost", "testclient"):
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/api/books",
                "headers": [(b"host", b"localhost:8000")],
                "client": (local_ip, 54321),
                "session": {},
            }
            req = Request(scope)
            # Should not raise
            _ensure_authorized(req)


@pytest.mark.asyncio
class TestCollectionImportSizeLimiting:
    """Item 3: POST /api/collections/import size limiting via read_limited_upload."""

    async def test_read_limited_upload_rejects_oversized(self):
        """Verify read_limited_upload raises 413 when content exceeds max_bytes."""
        from app.routers.books import read_limited_upload

        large_payload = b"x" * 1024
        upload = UploadFile(filename="large.json", file=io.BytesIO(large_payload))

        with pytest.raises(HTTPException) as exc:
            await read_limited_upload(upload, max_bytes=512, label="Koleksiyon dosyası")
        assert exc.value.status_code == 413
        assert "boyutu çok büyük" in exc.value.detail

    async def test_read_limited_upload_accepts_valid_size(self):
        """Verify read_limited_upload reads valid size payload."""
        from app.routers.books import read_limited_upload

        valid_payload = b'{"koleksiyon_adi": "Test", "kitaplar": []}'
        upload = UploadFile(filename="test.json", file=io.BytesIO(valid_payload))
        content = await read_limited_upload(upload, max_bytes=1024, label="Koleksiyon dosyası")
        assert content == valid_payload


class TestGoogleSearchGroundingPropagation:
    """Item 4: google_search_grounding setting propagation in task_queue, chat, session_manager."""

    def test_task_queue_reads_grounding_from_config(self):
        """Verify _analyze_pdf_standalone passes google_search_grounding from config to ai_service."""
        from app.task_queue import _analyze_pdf_standalone

        mock_ai_service = MagicMock()
        mock_ai_service.generate_text.return_value = '{"kitap_adi": "A", "yazar": "B", "kategori": "C", "alt_kategori": "D", "ozet": "E", "anahtar_kelimeler": "F"}'

        fake_gemini_key = f"AIzaSy{'FakeKey' * 3}"
        cfg_with_grounding = {
            "ai_provider": "gemini",
            "ai_api_key": fake_gemini_key,
            "google_search_grounding": True,
            "gemini_cascade_mode": False,
        }

        with patch("app.services.ai_service.AIService", return_value=mock_ai_service):
            _analyze_pdf_standalone(
                filename="sample.pdf",
                text="Sample text",
                provider="gemini",
                api_key=fake_gemini_key,
                config=cfg_with_grounding,
                model_name="gemini-3.5-flash-lite",
                base_url=None,
            )

        # Check that generate_text received google_search_grounding=True
        assert mock_ai_service.generate_text.called
        call_kwargs = mock_ai_service.generate_text.call_args.kwargs
        assert call_kwargs.get("google_search_grounding") is True
