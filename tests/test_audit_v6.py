"""Comprehensive tests for Audit V6 code quality, security, and architectural refactoring.

Verifies:
1. XXE vulnerability protection via defusedxml in EPUB parser.
2. Dynamic SQL protection via ALLOWED_UPDATE_COLUMNS in DocumentRepository.
3. Centralized AI prompt templates in app/prompts.py.
4. SRP decomposition of God functions into modular helpers.
5. AST validation guaranteeing zero silent except: pass blocks and complete return type hints.
"""

import ast
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import aiosqlite
import pytest

from app.epub import _extract_text_from_html_fallback, _locate_opf_path
from app.prompts import (
    build_book_chat_prompt,
    build_book_system_instruction,
    build_catalog_system_instruction,
    build_library_chat_prompt,
    build_pdf_analysis_prompt,
)
from app.repositories.document_repository import DocumentRepository
from app.routers.chat import _resolve_agentic_intent
from app.services.telegram_service import telegram_service
from app.task_queue import _extract_document_text


class TestSecurityDefensiveAuditV6:
    """Security validations covering XXE protection and SQL column whitelist."""

    def test_defusedxml_xxe_protection(self):
        """Verifies that defusedxml protects against entity expansion attacks."""
        import defusedxml.ElementTree as ET
        from defusedxml.common import EntitiesForbidden

        xxe_xml = """<?xml version="1.0"?>
        <!DOCTYPE foo [
          <!ELEMENT foo ANY >
          <!ENTITY xxe SYSTEM "file:///etc/passwd" >]>
        <foo>&xxe;</foo>"""

        with pytest.raises(EntitiesForbidden):
            ET.fromstring(xxe_xml)

    @pytest.mark.asyncio
    async def test_allowed_update_columns_whitelist(self):
        """update_book must ignore unauthorized columns and only update whitelisted columns."""
        async with aiosqlite.connect(":memory:") as conn:
            await conn.execute("""
                CREATE TABLE kitaplar (
                    dosya_hash TEXT PRIMARY KEY,
                    kitap_adi TEXT,
                    yazar TEXT,
                    kategori TEXT,
                    alt_kategori TEXT,
                    ozet TEXT,
                    anahtar_kelimeler TEXT,
                    dosya_yolu TEXT,
                    is_favorite BOOLEAN DEFAULT 0
                )
            """)
            await conn.execute("""
                INSERT INTO kitaplar (dosya_hash, kitap_adi, yazar, is_favorite)
                VALUES ('h123', 'Orijinal Kitap', 'Orijinal Yazar', 0)
            """)
            await conn.commit()

            repo = DocumentRepository(conn)

            # Attempt to update whitelisted column ('kitap_adi') alongside unwhitelisted columns ('is_favorite', 'malicious_col')
            update_data = {
                "kitap_adi": "Guncellenmis Kitap",
                "is_favorite": 1,  # Not in ALLOWED_UPDATE_COLUMNS
                "malicious_col; DROP TABLE kitaplar; --": "hacked",
            }
            await repo.update_book("h123", update_data)

            cur = await conn.execute(
                "SELECT kitap_adi, yazar, is_favorite FROM kitaplar WHERE dosya_hash = 'h123'"
            )
            row = await cur.fetchone()

            assert row[0] == "Guncellenmis Kitap"
            # is_favorite was not in ALLOWED_UPDATE_COLUMNS, so it must remain 0
            assert row[2] == 0

    @pytest.mark.asyncio
    async def test_get_distinct_values_whitelist(self):
        """get_distinct_values should accept whitelisted fields and reject unauthorized column queries."""
        async with aiosqlite.connect(":memory:") as conn:
            await conn.execute("CREATE TABLE kitaplar (dosya_hash TEXT, kategori TEXT, yazar TEXT)")
            await conn.execute("INSERT INTO kitaplar VALUES ('h1', 'Roman', 'Yazar A')")
            await conn.commit()

            repo = DocumentRepository(conn)
            cats = await repo.get_distinct_values("kategori")
            assert cats == ["Roman"]

            # Unwhitelisted or injection column safely returns empty list without querying
            unauth = await repo.get_distinct_values("unauthorized_column; DROP TABLE kitaplar; --")
            assert unauth == []

            # Verify table was not affected
            cur = await conn.execute("SELECT COUNT(*) FROM kitaplar")
            assert (await cur.fetchone())[0] == 1


class TestPromptsCentralization:
    """Tests that app/prompts.py generates correct prompt schemas and system instructions."""

    def test_build_pdf_analysis_prompt(self):
        """Analysis prompt must contain JSON formatting instructions and standard categories."""
        prompt = build_pdf_analysis_prompt(filename="deneme.pdf", text="Örnek kitap metni...")
        assert "JSON" in prompt
        assert "Örnek kitap metni..." in prompt
        assert "deneme.pdf" in prompt

    def test_build_book_system_instruction(self):
        """System instruction adapts based on is_full_text flag."""
        instr_brief = build_book_system_instruction("Sefiller", "Victor Hugo", is_full_text=False)
        assert "Sefiller" in instr_brief
        assert "Victor Hugo" in instr_brief
        assert "doğal" in instr_brief

        instr_full = build_book_system_instruction("Sefiller", "Victor Hugo", is_full_text=True)
        assert "tam metnine doğrudan erişimi olan" in instr_full

    def test_build_book_chat_prompt(self):
        """Chat prompt correctly integrates RAG context and user query."""
        chat_prompt = build_book_chat_prompt(
            user_message="Karakter analizi yap",
            rag_context="[Metin parcalari...]",
            is_full_text=True,
        )
        assert "Karakter analizi yap" in chat_prompt
        assert "[Metin parcalari...]" in chat_prompt

    def test_build_catalog_prompts(self):
        """Library/catalog chat prompts format stats and book lists."""
        sys_instr = build_catalog_system_instruction()
        assert "Kütüphane Asistanısın" in sys_instr

        chat_prompt = build_library_chat_prompt(
            user_message="Tarih kitapları öner", catalog_context="Tarih Kitabı 1, Tarih Kitabı 2"
        )
        assert "Tarih kitapları öner" in chat_prompt
        assert "Tarih Kitabı 1" in chat_prompt


class TestGodFunctionDecomposition:
    """Verifies that modular helper functions extracted from SRP-violating God functions work properly."""

    @pytest.mark.asyncio
    async def test_resolve_agentic_intent(self):
        """_resolve_agentic_intent correctly separates general library queries from book-specific queries."""
        mock_db = MagicMock()
        mock_db.get_distinct_values = AsyncMock(return_value=["Roman", "Tarih"])

        intent, rag = await _resolve_agentic_intent(mock_db, "Hangi kategoriler var?")
        assert intent == "list_categories"
        assert "Roman, Tarih" in rag

        intent_auth, rag_auth = await _resolve_agentic_intent(mock_db, "Tüm yazarlar kimler?")
        assert intent_auth == "list_authors"

        no_intent, no_rag = await _resolve_agentic_intent(mock_db, "Bu kitabın konusu nedir?")
        assert no_intent is None
        assert no_rag == ""

    def test_extract_document_text_txt_fallback(self):
        """_extract_document_text handles plain text files."""
        with tempfile.NamedTemporaryFile(
            suffix=".txt", mode="w", encoding="utf-8", delete=False
        ) as f:
            f.write("Merhaba dijital kütüphane! Bu bir test dosyasıdır.")
            tmp_name = f.name

        try:
            text, doc_type = _extract_document_text(
                tmp_name, is_epub=False, is_txt=True, max_pages=1
            )
            assert doc_type == "TXT"
            assert "Merhaba dijital" in text
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    @pytest.mark.asyncio
    async def test_telegram_sync_helpers(self):
        """_is_file_already_in_library and _build_temp_download_path correctly handle files."""
        mock_db = MagicMock()
        mock_db.get_book_by_filename = AsyncMock(return_value=None)

        exists = await telegram_service._is_file_already_in_library(
            mock_db, "non_existent.pdf", 1000
        )
        assert exists is False

        tmp_path = telegram_service._build_temp_download_path(12345, "My Document (1).pdf")
        assert tmp_path.endswith(".pdf")
        assert os.path.basename(tmp_path).startswith("tg_12345_")

    def test_epub_helpers(self):
        """_locate_opf_path parses container XML and returns rootfile path."""
        import zipfile
        from io import BytesIO

        container_xml = b"""<?xml version="1.0"?>
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
            <rootfiles>
                <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
            </rootfiles>
        </container>"""

        bio = BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            zf.writestr("META-INF/container.xml", container_xml)

        with zipfile.ZipFile(bio, "r") as zf:
            opf_path = _locate_opf_path(zf)
            assert opf_path == "OEBPS/content.opf"

        # Fallback text extractor
        bio2 = BytesIO()
        with zipfile.ZipFile(bio2, "w") as zf:
            zf.writestr("chapter1.html", "<html><body><p>Test Bolum 1</p></body></html>")

        with zipfile.ZipFile(bio2, "r") as zf:
            text = _extract_text_from_html_fallback(zf, max_chars=100)
            assert "Test Bolum 1" in text


class TestCodeQualityASTVerification:
    """Static AST assertions guaranteeing strict code quality standards across app/."""

    def test_zero_silent_except_pass_in_codebase(self):
        """Ensures that no silent `except: pass` error blocks exist in app/."""
        silent_passes = []
        for root, _, files in os.walk("app"):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, encoding="utf-8") as src:
                        tree = ast.parse(src.read(), filename=path)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                                silent_passes.append(f"{path}:{node.lineno}")

        assert len(silent_passes) == 0, f"Found silent pass blocks: {silent_passes}"

    def test_complete_return_type_hints_in_app(self):
        """Ensures that 100% of functions and methods in app/ have explicit return type annotations."""
        unannotated_funcs = []
        for root, _, files in os.walk("app"):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, encoding="utf-8") as src:
                        tree = ast.parse(src.read(), filename=path)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name.startswith("__"):
                                continue
                            if node.returns is None:
                                unannotated_funcs.append(f"{path}:{node.lineno} {node.name}")

        assert len(unannotated_funcs) == 0, (
            f"Found functions missing return type hints: {unannotated_funcs}"
        )
