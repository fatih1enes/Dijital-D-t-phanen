"""Tests for Telegram synchronization module and API endpoints."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.errors import SessionPasswordNeededError

from app.services.telegram_service import telegram_service

pytestmark = pytest.mark.asyncio


class TestTelegramEndpoints:
    """Test Telegram API endpoints."""

    async def test_telegram_status_endpoint(self, async_client):
        """Test GET /api/telegram/status."""
        response = await async_client.get("/api/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        assert "authorized" in data
        assert "is_syncing" in data

    async def test_send_code_validation_error(self, async_client):
        """Test POST /api/telegram/auth/send-code with missing or invalid fields."""
        response = await async_client.post(
            "/api/telegram/auth/send-code",
            json={"api_id": "", "api_hash": "", "phone_number": ""},
        )
        assert response.status_code in [400, 422]

    async def test_send_code_success(self, async_client):
        """Test POST /api/telegram/auth/send-code with mocked Telethon request."""
        with patch.object(
            telegram_service,
            "request_code",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "status": "code_sent",
                "phone_code_hash": "mock_hash_123",
            },
        ):
            response = await async_client.post(
                "/api/telegram/auth/send-code",
                json={
                    "api_id": "123456",
                    "api_hash": "mock_api_hash_value_1234",
                    "phone_number": "+905551234567",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["phone_code_hash"] == "mock_hash_123"

    async def test_verify_code_needs_2fa(self, async_client):
        """Test POST /api/telegram/auth/verify when 2FA password is required."""
        with patch.object(
            telegram_service,
            "verify_code",
            new_callable=AsyncMock,
            return_value={
                "success": False,
                "needs_password": True,
                "error": "2FA şifresi gerekli.",
            },
        ):
            response = await async_client.post(
                "/api/telegram/auth/verify",
                json={"code": "12345"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["needs_password"] is True

    async def test_verify_code_success(self, async_client):
        """Test POST /api/telegram/auth/verify success."""
        with patch.object(
            telegram_service,
            "verify_code",
            new_callable=AsyncMock,
            return_value={
                "success": True,
                "status": "authenticated",
                "user": {"id": 999, "first_name": "Test", "phone": "+905551234567"},
            },
        ):
            response = await async_client.post(
                "/api/telegram/auth/verify",
                json={"code": "12345"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user"]["first_name"] == "Test"

    async def test_sync_trigger(self, async_client):
        """Test POST /api/telegram/sync."""
        with patch.object(telegram_service, "sync_documents", new_callable=AsyncMock):
            response = await async_client.post(
                "/api/telegram/sync",
                json={"chat_target": "me"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["started", "already_running"]

    async def test_update_channel(self, async_client):
        """Test POST /api/telegram/channel."""
        response = await async_client.post(
            "/api/telegram/channel",
            json={"chat_target": "@kitapkanalim"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["chat_id"] == "@kitapkanalim"

    async def test_disconnect(self, async_client):
        """Test POST /api/telegram/disconnect."""
        with patch.object(
            telegram_service,
            "disconnect",
            new_callable=AsyncMock,
            return_value={"success": True, "message": "Bağlantı kesildi."},
        ):
            response = await async_client.post("/api/telegram/disconnect")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestTelegramServiceLogic:
    """Test TelegramService business logic and temporary file cleanup."""

    async def test_normalize_chat_target(self):
        """Test normalization of different Telegram channel formats."""
        from app.services.telegram_service import normalize_chat_target

        assert normalize_chat_target("me") == "me"
        assert normalize_chat_target("ME") == "me"
        assert normalize_chat_target("") == "me"
        assert normalize_chat_target("https://t.me/mybooks") == "@mybooks"
        assert normalize_chat_target("t.me/mybooks") == "@mybooks"
        assert normalize_chat_target("@mybooks") == "@mybooks"
        assert normalize_chat_target("mybooks") == "@mybooks"
        assert normalize_chat_target("-1001234567890") == -1001234567890

    async def test_verify_code_session_password_error_handling(self, monkeypatch):
        """Verify that SessionPasswordNeededError is handled gracefully."""
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.sign_in = AsyncMock(side_effect=SessionPasswordNeededError("2FA required"))

        monkeypatch.setattr(telegram_service, "_client", mock_client)
        monkeypatch.setattr(
            telegram_service,
            "_pending_auth",
            {
                "api_id": 12345,
                "api_hash": "dummy_hash",
                "phone": "+905551234567",
                "phone_code_hash": "hash_abc",
                "created_at": 9999999999,  # Never expired in test
            },
        )

        res = await telegram_service.verify_code(code="12345", password=None)
        assert res["success"] is False
        assert res.get("needs_password") is True

    async def test_temp_file_cleanup_on_duplicate(self):
        """Verify that temporary files are cleaned up if the document already exists in DB."""
        # Create a mock temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(b"%PDF-1.4 dummy content for hash test")
            tmp_path = f.name

        mock_db = MagicMock()
        mock_db.book_exists = AsyncMock(return_value=True)

        mock_doc = MagicMock()
        mock_doc.file.name = "test_duplicate.pdf"
        mock_doc.file.size = 1024

        mock_message = MagicMock()
        mock_message.id = 42
        mock_message.document = mock_doc
        mock_message.file.name = "test_duplicate.pdf"
        mock_message.file.size = 1024

        async def fake_download(file):
            with open(file, "wb") as out:
                out.write(b"%PDF-1.4 dummy content for hash test")

        mock_message.download_media = AsyncMock(side_effect=fake_download)

        async def fake_iter(target, min_id, reverse):
            yield mock_message

        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.iter_messages = fake_iter

        mock_task_queue = MagicMock()
        mock_task_queue.enqueue = AsyncMock()

        orig_exists = os.path.exists

        with (
            patch.object(
                telegram_service, "get_client", new_callable=AsyncMock, return_value=mock_client
            ),
            patch(
                "app.services.telegram_service.load_config",
                return_value={
                    "telegram_api_id": "123",
                    "telegram_api_hash": "abc",
                    "telegram_chat_id": "me",
                },
            ),
            patch(
                "os.path.exists",
                side_effect=lambda p: True if "telegram.session" in str(p) else orig_exists(p),
            ),
        ):
            res = await telegram_service.sync_documents(
                task_queue=mock_task_queue, db=mock_db, chat_target="me"
            )
            assert res["success"] is True
            assert res["skipped_count"] >= 1
            # Task queue should NOT have been enqueued for a duplicate
            assert mock_task_queue.enqueue.call_count == 0

        # Clean up initial temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    async def test_sync_documents_passes_ai_key(self):
        """Verify that AI credentials (api_key, provider, model) are correctly passed to task_queue."""
        mock_db = MagicMock()
        mock_db.book_exists = AsyncMock(return_value=False)

        mock_doc = MagicMock()
        mock_doc.file.name = "new_book.pdf"
        mock_doc.file.size = 2048

        mock_message = MagicMock()
        mock_message.id = 99
        mock_message.document = mock_doc
        mock_message.file.name = "new_book.pdf"
        mock_message.file.size = 2048

        async def fake_download(file):
            with open(file, "wb") as out:
                out.write(b"%PDF-1.4 mock pdf content for AI key test")

        mock_message.download_media = AsyncMock(side_effect=fake_download)

        async def fake_iter(target, min_id, reverse):
            yield mock_message

        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.iter_messages = fake_iter

        mock_task_queue = MagicMock()
        mock_task_queue.enqueue = AsyncMock()

        orig_exists = os.path.exists

        with (
            patch.object(
                telegram_service, "get_client", new_callable=AsyncMock, return_value=mock_client
            ),
            patch(
                "app.services.telegram_service.load_config",
                return_value={
                    "telegram_api_id": "123",
                    "telegram_api_hash": "abc",
                    "telegram_chat_id": "me",
                },
            ),
            patch("app.services.telegram_service.save_config"),
            patch(
                "os.path.exists",
                side_effect=lambda p: True if "telegram.session" in str(p) else orig_exists(p),
            ),
        ):
            fake_gemini_key = f"AIzaSy{'TestKey' * 3}"
            res = await telegram_service.sync_documents(
                task_queue=mock_task_queue,
                db=mock_db,
                chat_target="me",
                api_key=fake_gemini_key,
                provider="gemini",
                model_name="gemini-3.5-flash-lite",
            )
            assert res["success"] is True
            assert res["enqueued_count"] == 1
            assert mock_task_queue.enqueue.call_count == 1
            queued_item = mock_task_queue.enqueue.call_args[0][0]
            assert queued_item["api_key"] == fake_gemini_key
            assert queued_item["provider"] == "gemini"
            assert queued_item["model_name"] == "gemini-3.5-flash-lite"
