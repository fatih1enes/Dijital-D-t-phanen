"""Unit tests verifying fixes for audit v4:
1. resolve_ai_credentials helper (DRY credential resolution)
2. Vision fallback functionality (render_pdf_vision_pages, create_vision_pdf, queue integration)
3. Clean DI and service layer (DocumentService removal, dependencies cleanup, AIRouter cleanup)
"""

import os
from unittest.mock import patch

import pytest

from app.config import load_config, resolve_ai_credentials
from app.constants import DEFAULT_GEMINI_MODEL


class TestResolveAICredentials:
    """Item 1: DRY AI credential resolution."""

    def test_header_precedence_over_config_and_env(self):
        cfg = {
            "ai_provider": "gemini",
            "ai_api_key": "config_gemini_key",
            "gemini_model": "gemini-3.7-flash",
        }
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env_gemini_key"}):
            prov, key, model, base_url = resolve_ai_credentials(
                provider="gemini",
                api_key="header_real_key_123",
                model="gemini-3.8-flash",
                base_url="https://custom.api",
                cfg=cfg,
            )
            assert prov == "gemini"
            assert key == "header_real_key_123"
            assert model == "gemini-3.8-flash"
            assert base_url == "https://custom.api"

    def test_masked_header_falls_back_to_config(self):
        cfg = {"ai_provider": "gemini", "ai_api_key": "config_real_key_456"}
        prov, key, model, base_url = resolve_ai_credentials(
            provider=None,
            api_key="••••••••",
            model=None,
            base_url=None,
            cfg=cfg,
        )
        assert key == "config_real_key_456"
        assert prov == "gemini"
        assert model == DEFAULT_GEMINI_MODEL

    def test_env_fallback_when_config_and_header_missing(self):
        cfg = {"ai_provider": "gemini", "ai_api_key": ""}
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env_fallback_key_789"}):
            prov, key, model, base_url = resolve_ai_credentials(
                provider=None,
                api_key=None,
                model=None,
                base_url=None,
                cfg=cfg,
            )
            assert key == "env_fallback_key_789"

    def test_ollama_local_provider(self):
        cfg = {"ai_provider": "ollama", "ollama_model": "llama3.2"}
        prov, key, model, base_url = resolve_ai_credentials(
            provider="ollama",
            api_key=None,
            model=None,
            base_url="http://localhost:11434/v1",
            cfg=cfg,
        )
        assert prov == "ollama"
        assert key == ""
        assert model == "llama3.2"
        assert base_url == "http://localhost:11434/v1"


class TestVisionPdfProcessing:
    """Item 2: Vision PDF rendering and fallback."""

    def test_render_pdf_vision_pages_and_create_vision_pdf(self, sample_pdf_bytes, tmp_path):
        from app.pdf import create_vision_pdf, render_pdf_vision_pages

        pdf_path = str(tmp_path / "test_doc.pdf")
        with open(pdf_path, "wb") as f:
            f.write(sample_pdf_bytes)

        # 1. Test render_pdf_vision_pages
        images = render_pdf_vision_pages(pdf_path, max_pages=5, max_dim=600, quality=80)
        assert len(images) >= 1
        for img in images:
            assert max(img.width, img.height) <= 600
            assert img.mode == "RGB"

        # 2. Test create_vision_pdf
        vision_pdf = create_vision_pdf(pdf_path, max_pages=5, max_dim=600, quality=80)
        assert vision_pdf is not None
        assert os.path.exists(vision_pdf)
        assert os.path.getsize(vision_pdf) > 0
        os.unlink(vision_pdf)

    def test_vision_config_defaults(self):
        cfg = load_config()
        assert "vision_pages" in cfg
        assert "vision_max_image_dim" in cfg
        assert "vision_jpeg_quality" in cfg
        assert cfg["vision_pages"] == 20
        assert cfg["vision_max_image_dim"] == 1200
        assert cfg["vision_jpeg_quality"] == 82


class TestCleanArchitecture:
    """Item 3: Clean DI and removed dead code."""

    def test_document_service_module_removed(self):
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.document_service")

    def test_dependencies_module_only_has_get_db(self):
        import app.dependencies as deps

        assert hasattr(deps, "get_db")
        assert not hasattr(deps, "get_document_service")
        assert not hasattr(deps, "get_ai_service")
        assert not hasattr(deps, "get_settings")

    def test_ai_router_class_removed(self):
        import app.ai_router as air

        assert hasattr(air, "generate_ai_response")
        assert not hasattr(air, "AIRouter")
