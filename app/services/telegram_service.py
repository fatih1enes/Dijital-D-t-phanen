"""Telegram synchronization service using Telethon for Dijital Kütüphane.

Provides pure async Telethon authentication, message scanning, document downloading,
and seamless queueing into the existing TaskQueue pipeline without blocking the event loop.
"""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any

from telethon import TelegramClient
from telethon.errors import (
    ApiIdInvalidError,
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)

from app.config import load_config, save_config
from app.constants import DATA_DIR, DEFAULT_GEMINI_MODEL, MAX_UPLOAD_BYTES
from app.logger import log_event, notify_ws
from app.tasks import active_tasks
from app.utils import get_file_hash_from_path, is_path_within, sanitize_filename

logger = logging.getLogger(__name__)

# Telethon automatically appends '.session' to SQLiteSession paths.
# Storing as 'veriler/telegram' generates 'veriler/telegram.session'.
SESSION_PATH = os.path.join(DATA_DIR, "telegram")
SESSION_FILE = f"{SESSION_PATH}.session"
TEMP_TELEGRAM_DIR = os.path.join(DATA_DIR, "temp_telegram")


def _secure_session_file() -> None:
    """Ensure Telegram session file permissions are restricted to owner only (0o600)."""
    if os.path.exists(SESSION_FILE) and hasattr(os, "chmod"):
        try:
            os.chmod(SESSION_FILE, 0o600)
        except OSError as e:
            logger.debug("Could not chmod session file %s: %s", SESSION_FILE, e)


def _mask_phone(phone: str) -> str:
    """Mask phone number for safe logging without exposing PII."""
    p = str(phone or "").strip()
    if len(p) <= 6:
        return "***"
    return f"{p[:5]}***{p[-4:]}"


def normalize_chat_target(raw_target: str) -> str | int:
    """Normalize Telegram chat/channel target (handles @channel, links, Turkish names, and integer IDs)."""
    t = str(raw_target or "me").strip()
    if not t or t.lower() in (
        "me",
        "kayıtlı mesajlar",
        "kayitli mesajlar",
        "saved messages",
        "saved",
    ):
        return "me"
    if "t.me/" in t:
        parts = t.split("t.me/")
        t = parts[-1].strip("/")
    try:
        return int(t)
    except ValueError as ve:
        logger.debug("Target '%s' is not an integer chat ID: %s", t, ve)
    if not t.startswith("@") and not t.startswith("-") and not t.isdigit():
        return f"@{t}"
    return t


def setup_telethon_optimizations() -> str:
    """Detect Telethon acceleration engine and configure optimal transfer chunk sizing."""
    engine = "pyaes (standart)"
    try:
        import telethon.crypto.aes as aes

        if getattr(aes, "cryptg", None) is not None:
            engine = "cryptg (native C)"
    except Exception as e:
        logger.debug("Telethon cryptg tespiti atlandı: %s", e)

    try:
        import telethon.utils as utils

        orig_part_size = getattr(utils, "_orig_get_appropriated_part_size", None)
        if orig_part_size is None:
            utils._orig_get_appropriated_part_size = utils.get_appropriated_part_size

            def fast_part_size(file_size: int) -> int:
                if file_size and file_size > 5 * 1024 * 1024:
                    return 512
                return utils._orig_get_appropriated_part_size(file_size)

            utils.get_appropriated_part_size = fast_part_size
    except Exception as e:
        logger.debug("Telethon chunk optimizasyonu atlandı: %s", e)

    return engine


class TelegramService:
    """Singleton service for managing Telethon client connection, authentication and synchronization."""

    def __init__(self):
        self._client: TelegramClient | None = None
        self._pending_auth: dict | None = None
        self._is_syncing: bool = False
        self._lock = asyncio.Lock()
        self._accel_engine = setup_telethon_optimizations()
        log_event(
            "telegram",
            "INFO",
            f"Telegram C-hızlandırma motoru aktif: {self._accel_engine}",
        )

    async def get_client(
        self, api_id: int | str | None = None, api_hash: str | None = None
    ) -> TelegramClient | None:
        """Get or initialize an asynchronous TelegramClient."""
        cfg = load_config()
        active_api_id = api_id or os.environ.get("TELEGRAM_API_ID") or cfg.get("telegram_api_id")
        active_api_hash = (
            api_hash or os.environ.get("TELEGRAM_API_HASH") or cfg.get("telegram_api_hash")
        )

        if not active_api_id or not active_api_hash:
            return None

        try:
            int_api_id = int(active_api_id)
        except (ValueError, TypeError):
            return None

        if self._client is not None:
            if not self._client.is_connected():
                await self._client.connect()
            return self._client

        os.makedirs(DATA_DIR, exist_ok=True)
        # Note: NEVER use client.start() as it is blocking and prompts via CLI
        client = TelegramClient(SESSION_PATH, int_api_id, str(active_api_hash).strip())
        await client.connect()
        _secure_session_file()
        self._client = client
        return self._client

    @staticmethod
    def _matches_dialog(d: Any, str_target: str) -> bool:
        """Check if a dialog entity matches target id, username, or title."""
        d_entity = getattr(d, "entity", None)
        if not d_entity:
            return False
        d_id = getattr(d_entity, "id", None)
        d_username = getattr(d_entity, "username", "") or ""
        d_title = getattr(d_entity, "title", "") or ""

        if d_id is not None:
            candidates = [str(d_id), f"-{d_id}", f"-100{d_id}", str(getattr(d, "id", ""))]
            if str_target in candidates or str_target.removeprefix("-100") == str(d_id):
                return True

        if d_username and str_target.lstrip("@").lower() == d_username.lower():
            return True

        return bool(d_title and str_target.lower() == d_title.lower())

    async def resolve_chat_entity(self, client: TelegramClient, target: str | int) -> Any:
        """Safely resolve Telegram chat entity, fetching dialogs if uncached or ID format varies."""
        if isinstance(target, str) and target.lower() == "me":
            return "me"

        try:
            return await client.get_input_entity(target)
        except Exception as ent_err:
            logger.debug("Target not found in initial entity cache: %s", ent_err)

        # If uncached, fetch all dialogs to populate Telethon's local entity cache
        try:
            dialogs = await client.get_dialogs()
            str_target = str(target).strip()

            # Try direct resolution after populating cache
            try:
                return await client.get_input_entity(target)
            except Exception as ent_err2:
                logger.debug("Target entity resolution failed after dialog fetch: %s", ent_err2)

            # Search in dialogs for matching id, username, or title
            for d in dialogs:
                if self._matches_dialog(d, str_target):
                    return await client.get_input_entity(d.entity)
        except Exception as dialog_err:
            log_event("telegram", "WARNING", f"Dialog tarama hatası: {dialog_err}")

        return target

    async def check_status(self) -> dict:
        """Check current Telegram connection and authorization status."""
        cfg = load_config()
        has_session_file = os.path.exists(SESSION_FILE)
        api_id = cfg.get("telegram_api_id", "")
        api_hash = cfg.get("telegram_api_hash", "")
        chat_id = cfg.get("telegram_chat_id", "me")
        last_sync = cfg.get("telegram_last_sync", "")

        status_data = {
            "has_session": has_session_file,
            "connected": False,
            "authorized": False,
            "is_syncing": self._is_syncing,
            "phone": "",
            "username": "",
            "first_name": "",
            "chat_id": chat_id,
            "last_sync": last_sync,
            "api_id": str(api_id) if api_id else "",
            "has_api_hash": bool(api_hash),
        }

        if not has_session_file or not api_id or not api_hash:
            return status_data

        try:
            client = await self.get_client(api_id, api_hash)
            if client and client.is_connected():
                is_auth = await client.is_user_authorized()
                status_data["connected"] = True
                status_data["authorized"] = is_auth
                if is_auth:
                    me = await client.get_me()
                    if me:
                        status_data["phone"] = getattr(me, "phone", "") or ""
                        status_data["username"] = getattr(me, "username", "") or ""
                        status_data["first_name"] = getattr(me, "first_name", "") or ""
        except Exception as e:
            log_event("telegram", "WARNING", f"Telegram durum kontrolü hatası: {e}")

        return status_data

    async def request_code(
        self,
        api_id: int | str,
        api_hash: str,
        phone: str,
        chat_target: str | None = None,
    ) -> dict:
        """Initiate authentication by requesting SMS/app confirmation code from Telegram."""
        async with self._lock:
            if not api_id or not api_hash or not phone:
                return {
                    "success": False,
                    "error": "API ID, API Hash ve Telefon Numarası zorunludur.",
                }

            if chat_target:
                cfg = load_config()
                cfg["telegram_chat_id"] = str(chat_target).strip()
                save_config(cfg)

            try:
                int_api_id = int(api_id)
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": "Geçersiz API ID. Lütfen sayısal bir değer girin.",
                }

            # Safely disconnect any previously active client to release session lock
            if self._client is not None:
                try:
                    await self._client.disconnect()
                except Exception as disc_err:
                    logger.debug("Could not disconnect previous client: %s", disc_err)
                self._client = None

            os.makedirs(DATA_DIR, exist_ok=True)
            client = TelegramClient(SESSION_PATH, int_api_id, str(api_hash).strip())
            await client.connect()
            _secure_session_file()

            try:
                # Strictly async send_code_request
                code_req = await client.send_code_request(str(phone).strip())
                self._pending_auth = {
                    "api_id": int_api_id,
                    "api_hash": str(api_hash).strip(),
                    "phone": str(phone).strip(),
                    "phone_code_hash": code_req.phone_code_hash,
                    "created_at": time.time(),
                }
                self._client = client

                log_event("telegram", "INFO", f"Telegram doğrulama kodu talep edildi: {_mask_phone(phone)}")
                return {
                    "success": True,
                    "status": "code_sent",
                    "phone_code_hash": code_req.phone_code_hash,
                    "message": "Doğrulama kodu Telegram uygulamanıza veya SMS ile gönderildi.",
                }
            except PhoneNumberInvalidError:
                await client.disconnect()
                return {
                    "success": False,
                    "error": "Geçersiz telefon numarası. Lütfen ülke koduyla birlikte girin (+90...)",
                }
            except ApiIdInvalidError:
                await client.disconnect()
                return {
                    "success": False,
                    "error": "Geçersiz API ID veya API Hash bilgisi.",
                }
            except FloodWaitError as e:
                await client.disconnect()
                return {
                    "success": False,
                    "error": f"Telegram istek sınırı (FloodWait). Lütfen {e.seconds} saniye sonra tekrar deneyin.",
                }
            except Exception as e:
                await client.disconnect()
                return {
                    "success": False,
                    "error": f"Kod gönderilirken hata oluştu: {str(e)}",
                }

    async def verify_code(self, code: str, password: str | None = None) -> dict:
        """Complete authentication using confirmation code and optional 2FA password."""
        async with self._lock:
            if not self._pending_auth:
                return {
                    "success": False,
                    "error": "Aktif bir doğrulama oturumu bulunamadı veya süre doldu. Lütfen tekrar kod talep edin.",
                }

            if time.time() - self._pending_auth.get("created_at", 0) > 600:
                self._pending_auth = None
                return {
                    "success": False,
                    "error": "Doğrulama oturumunun süresi doldu (10 dakika). Lütfen yeniden kod talep edin.",
                }

            phone = self._pending_auth["phone"]
            phone_code_hash = self._pending_auth["phone_code_hash"]
            api_id = self._pending_auth["api_id"]
            api_hash = self._pending_auth["api_hash"]

            client = self._client
            if client is None or not client.is_connected():
                client = TelegramClient(SESSION_PATH, api_id, api_hash)
                await client.connect()
                self._client = client

            awaiting_password = bool(self._pending_auth.get("awaiting_password"))
            clean_password = str(password).strip() if password else ""

            try:
                if awaiting_password or clean_password:
                    if not clean_password:
                        return {
                            "success": False,
                            "needs_password": True,
                            "error": "Hesabınızda İki Adımlı Doğrulama (2FA Bulut Şifresi) aktif. Lütfen şifrenizi girin.",
                        }
                    try:
                        await client.sign_in(password=clean_password)
                    except PasswordHashInvalidError:
                        return {
                            "success": False,
                            "needs_password": True,
                            "error": "Girdiğiniz 2FA şifresi hatalı.",
                        }
                else:
                    try:
                        # Attempt pure async sign_in with phone, code, phone_code_hash
                        await client.sign_in(
                            phone=phone,
                            code=str(code).strip(),
                            phone_code_hash=phone_code_hash,
                        )
                    except SessionPasswordNeededError:
                        # Two-step verification (2FA) is active on the Telegram account
                        self._pending_auth["awaiting_password"] = True
                        if not clean_password:
                            return {
                                "success": False,
                                "needs_password": True,
                                "error": "Hesabınızda İki Adımlı Doğrulama (2FA Bulut Şifresi) aktif. Lütfen şifrenizi girin.",
                            }
                        try:
                            await client.sign_in(password=clean_password)
                        except PasswordHashInvalidError:
                            return {
                                "success": False,
                                "needs_password": True,
                                "error": "Girdiğiniz 2FA şifresi hatalı.",
                            }
            except PhoneCodeInvalidError:
                return {"success": False, "error": "Girdiğiniz doğrulama kodu hatalı."}
            except PhoneCodeExpiredError:
                return {
                    "success": False,
                    "error": "Doğrulama kodunun süresi dolmuş. Lütfen yeni kod talep edin.",
                }
            except FloodWaitError as e:
                return {
                    "success": False,
                    "error": f"Çok fazla deneme yapıldı. Lütfen {e.seconds} saniye bekleyin.",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Doğrulama sırasında hata: {str(e)}",
                }

            # Authentication succeeded: persist credentials to config
            cfg = load_config()
            cfg["telegram_api_id"] = str(api_id)
            cfg["telegram_api_hash"] = str(api_hash)
            save_config(cfg)
            _secure_session_file()

            me = await client.get_me()
            user_info = {
                "id": getattr(me, "id", 0),
                "phone": getattr(me, "phone", "") or phone,
                "first_name": getattr(me, "first_name", "") or "",
                "username": getattr(me, "username", "") or "",
            }
            self._pending_auth = None

            log_event(
                "telegram",
                "INFO",
                f"Telegram bağlantısı başarıyla tamamlandı: {user_info['first_name']} ({_mask_phone(user_info['phone'])})",
            )
            notify_ws("telegram_status", {"authorized": True, "user": user_info})

            return {
                "success": True,
                "status": "authenticated",
                "message": "Telegram hesabı başarıyla bağlandı.",
                "user": user_info,
            }

    async def _is_file_already_in_library(self, db: Any, filename: str, doc_size: int) -> bool:
        """Check if a book with identical filename and size already exists in the library."""
        existing_row = None
        fn = getattr(db, "get_book_by_filename", None)
        if fn and callable(fn):
            try:
                import inspect

                check_call = fn(filename)
                if inspect.isawaitable(check_call):
                    existing_row = await check_call
                else:
                    existing_row = check_call
            except Exception:
                existing_row = None

        if (
            existing_row
            and len(existing_row) > 1
            and existing_row[1]
            and os.path.exists(existing_row[1])
        ):
            try:
                file_sz = os.path.getsize(existing_row[1])
                if doc_size == 0 or file_sz == doc_size:
                    log_event(
                        "telegram",
                        "INFO",
                        f"Kitap kütüphanede zaten kayıtlı, indirilmeden atlandı: {filename}",
                        file_hash=existing_row[0],
                    )
                    notify_ws(
                        "telegram_sync",
                        {
                            "status": "already_exists",
                            "filename": filename,
                            "message": f"Kitap kütüphanede zaten kayıtlı (Atlandı): {filename}",
                        },
                    )
                    return True
            except OSError as os_err:
                logger.debug("Could not inspect existing library file: %s", os_err)
        return False

    def _build_temp_download_path(self, message_id: int, filename: str) -> str | None:
        """Construct secure temporary download path within TEMP_TELEGRAM_DIR."""
        unique_prefix = f"tg_{message_id}_{uuid.uuid4().hex[:6]}"
        safe_name = f"{unique_prefix}_{filename}"
        tmp_path = os.path.join(TEMP_TELEGRAM_DIR, safe_name)
        if not is_path_within(TEMP_TELEGRAM_DIR, tmp_path):
            log_event(
                "telegram",
                "ERROR",
                f"Geçersiz veya dizin dışı dosya yolu atlandı: {filename}",
            )
            return None
        return tmp_path

    async def _perform_document_download(self, message: Any, tmp_path: str, filename: str) -> bool:
        """Download document media with throttled WebSocket progress reporting."""
        start_dl_time = time.time()
        last_ws_report = 0.0

        notify_ws(
            "telegram_sync",
            {
                "status": "downloading",
                "filename": filename,
                "percent": 0,
                "speed": "0.0 MB/s",
                "message": f"Telegram'dan indiriliyor: {filename}",
            },
        )

        def download_progress(received_bytes: int, total_bytes: int) -> None:
            nonlocal last_ws_report
            now = time.time()
            if now - last_ws_report >= 0.35 or (total_bytes and received_bytes >= total_bytes):
                last_ws_report = now
                elapsed = now - start_dl_time
                speed_mb = (received_bytes / (1024 * 1024)) / elapsed if elapsed > 0.05 else 0.0
                pct = round((received_bytes / total_bytes) * 100, 1) if total_bytes else 0
                notify_ws(
                    "telegram_sync",
                    {
                        "status": "downloading",
                        "filename": filename,
                        "percent": pct,
                        "speed": f"{speed_mb:.1f} MB/s",
                        "received": received_bytes,
                        "total": total_bytes,
                        "message": f"Telegram'dan indiriliyor (%{int(pct)} - {speed_mb:.1f} MB/s)",
                    },
                )

        try:
            try:
                await message.download_media(file=tmp_path, progress_callback=download_progress)
            except Exception as dl_inner_err:
                log_event(
                    "telegram",
                    "WARNING",
                    f"Optimize indirme uyarısı ({filename}), standart metoda geçiliyor: {dl_inner_err}",
                )
                await message.download_media(file=tmp_path)
            return True
        except Exception as e:
            log_event("telegram", "ERROR", f"Dosya indirme başarısız ({filename}): {e}")
            return False

    async def _enqueue_telegram_task(
        self,
        task_queue: Any,
        tmp_path: str,
        filename: str,
        file_hash: str,
        target: str | int,
        sync_creds: dict,
    ) -> str:
        """Create task queue entry and enqueue for asynchronous processing."""
        task_id = str(uuid.uuid4())
        task_entry = {
            "filename": filename,
            "status": "processing",
            "percentage": 5,
            "log_message": "Telegram'dan aktarıldı, kuyrukta bekliyor...",
            "last_update": time.time(),
            "logs": [
                {
                    "ts": time.time(),
                    "message": f"Telegram'dan aktarıldı ({target}), AI kuyruğuna alındı...",
                    "status": "processing",
                    "state": "pending",
                    "pct": 5,
                }
            ],
        }
        active_tasks[task_id] = task_entry

        log_event(
            "telegram",
            "INFO",
            f"Telegram belgesi indirildi ve AI kuyruğuna alındı: {filename}",
            task_id=task_id,
            filename=filename,
            file_hash=file_hash,
        )
        notify_ws("task", {"task_id": task_id, "task": task_entry})

        await task_queue.enqueue(
            {
                "task_id": task_id,
                "tmp_path": tmp_path,
                "filename": filename,
                "file_hash": file_hash,
                "provider": sync_creds["provider"],
                "api_key": sync_creds["api_key"],
                "config": sync_creds["config"],
                "model_name": sync_creds["model_name"],
                "base_url": sync_creds["base_url"],
            }
        )
        return task_id

    @staticmethod
    def _resolve_sync_credentials(
        cfg: dict,
        api_key: str | None,
        provider: str | None,
        model_name: str | None,
        base_url: str | None,
    ) -> dict[str, Any]:
        """Resolve active AI credentials and parameters for Telegram task processing."""
        from app.config import is_real_api_key

        given_key = str(api_key or "").strip()
        active_api_key = given_key if is_real_api_key(given_key) else ""
        if not active_api_key:
            cfg_key = str(cfg.get("ai_api_key") or "").strip()
            active_api_key = cfg_key if is_real_api_key(cfg_key) else ""
        if not active_api_key:
            env_key = str(os.environ.get("GEMINI_API_KEY") or "").strip()
            active_api_key = env_key if is_real_api_key(env_key) else ""

        active_provider = str(provider or cfg.get("ai_provider") or "gemini").strip().lower()
        active_model = model_name or cfg.get(f"{active_provider}_model")
        if not active_model and active_provider == "gemini":
            active_model = DEFAULT_GEMINI_MODEL
        active_base_url = str(base_url or cfg.get("ai_base_url") or "").strip()

        return {
            "api_key": active_api_key,
            "provider": active_provider,
            "model_name": active_model,
            "base_url": active_base_url,
            "config": cfg,
        }

    async def _process_single_sync_message(
        self,
        message: Any,
        db: Any,
        task_queue: Any,
        target: Any,
        sync_creds: dict,
    ) -> tuple[bool, bool, int]:
        """Process a single Telegram message. Returns (enqueued, skipped, seen_message_id)."""
        if not message.document:
            return False, False, 0

        raw_filename = os.path.basename(message.file.name or f"telegram_{message.id}.pdf")
        filename = sanitize_filename(raw_filename) or f"telegram_{message.id}.pdf"
        _, ext = os.path.splitext(filename)
        if ext.lower() not in (".pdf", ".epub", ".txt"):
            return False, False, 0

        doc_size = message.file.size or 0
        if doc_size > MAX_UPLOAD_BYTES:
            log_event(
                "telegram",
                "WARNING",
                f"Dosya boyutu çok büyük, atlandı ({round(doc_size / (1024 * 1024), 1)} MB): {filename}",
                filename=filename,
                size=doc_size,
            )
            return False, True, 0

        # Pre-check existing book in database
        if await self._is_file_already_in_library(db, filename, doc_size):
            return False, True, message.id

        # Download media to safe temporary path
        tmp_path = self._build_temp_download_path(message.id, filename)
        if not tmp_path:
            return False, True, 0

        enqueued = False
        try:
            downloaded = await self._perform_document_download(message, tmp_path, filename)
            if not downloaded or not os.path.exists(tmp_path):
                return False, False, 0

            file_hash = await asyncio.to_thread(get_file_hash_from_path, tmp_path)
            if await db.book_exists(file_hash):
                log_event(
                    "telegram",
                    "INFO",
                    f"Kitap kütüphanede zaten kayıtlı, atlandı: {filename}",
                    file_hash=file_hash,
                )
                notify_ws(
                    "telegram_sync",
                    {
                        "status": "already_exists",
                        "filename": filename,
                        "message": f"Kitap kütüphanede zaten kayıtlı: {filename}",
                    },
                )
                return False, True, message.id

            await self._enqueue_telegram_task(
                task_queue,
                tmp_path,
                filename,
                file_hash,
                target,
                sync_creds,
            )
            enqueued = True
            return True, False, message.id
        except Exception as dl_err:
            log_event(
                "telegram",
                "ERROR",
                f"Dosya işlenirken hata oluştu ({filename}): {dl_err}",
            )
            return False, False, 0
        finally:
            if not enqueued and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError as e:
                    log_event(
                        "filesystem",
                        "WARNING",
                        f"Geçici Telegram dosyası silinemedi ({tmp_path}): {e}",
                    )

    async def sync_documents(
        self,
        task_queue,
        db=None,
        chat_target: str | None = None,
        api_key: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        reset_cursor: bool = False,
    ) -> dict:
        """Scan Telegram messages chronologically, download supported books and enqueue to TaskQueue."""
        if db is None:
            from app.database import get_db_context

            async with get_db_context() as local_db:
                return await self.sync_documents(
                    task_queue,
                    db=local_db,
                    chat_target=chat_target,
                    api_key=api_key,
                    provider=provider,
                    model_name=model_name,
                    base_url=base_url,
                    reset_cursor=reset_cursor,
                )

        if self._is_syncing:
            return {
                "success": False,
                "error": "Senkronizasyon işlemi şu anda zaten devam ediyor.",
            }

        self._is_syncing = True
        last_msg_id = 0
        max_seen_id = 0
        try:
            cfg = load_config()
            api_id = cfg.get("telegram_api_id")
            api_hash = cfg.get("telegram_api_hash")

            if not api_id or not api_hash or not os.path.exists(SESSION_FILE):
                err_msg = "Telegram bağlantısı yapılandırılmamış veya oturum bulunamadı."
                notify_ws("telegram_sync", {"status": "error", "message": err_msg})
                return {"success": False, "error": err_msg}

            client = await self.get_client(api_id, api_hash)
            if not client or not client.is_connected() or not await client.is_user_authorized():
                err_msg = "Telegram oturumu yetkilendirilmemiş. Lütfen yeniden bağlanın."
                notify_ws("telegram_sync", {"status": "error", "message": err_msg})
                return {"success": False, "error": err_msg}

            raw_target = str(chat_target or cfg.get("telegram_chat_id") or "me").strip()
            target = normalize_chat_target(raw_target)

            # Reset last_msg_id if switching channels or if explicit reset requested
            old_saved_target = str(cfg.get("telegram_chat_id") or "me").strip()
            if reset_cursor or raw_target != old_saved_target:
                cfg["telegram_chat_id"] = raw_target
                cfg["telegram_last_msg_id"] = 0
                save_config(cfg)
                last_msg_id = 0
            else:
                last_msg_id = int(cfg.get("telegram_last_msg_id", 0) or 0)
            max_seen_id = last_msg_id

            sync_creds = self._resolve_sync_credentials(
                cfg, api_key, provider, model_name, base_url
            )
            os.makedirs(TEMP_TELEGRAM_DIR, exist_ok=True)

            notify_ws(
                "telegram_sync",
                {
                    "status": "started",
                    "chat": target,
                    "message": f"Telegram taranıyor: '{target}' (Son mesaj ID: {last_msg_id})...",
                },
            )
            log_event(
                "telegram",
                "INFO",
                f"Telegram senkronizasyonu başlatıldı. Hedef: '{target}', Son Mesaj ID: {last_msg_id}",
            )

            scanned_count = 0
            enqueued_count = 0
            skipped_count = 0

            try:
                resolved_target = await self.resolve_chat_entity(client, target)
                async for message in client.iter_messages(
                    resolved_target, min_id=last_msg_id, reverse=True
                ):
                    scanned_count += 1
                    enq, skp, msg_id = await self._process_single_sync_message(
                        message, db, task_queue, target, sync_creds
                    )
                    if enq:
                        enqueued_count += 1
                    if skp:
                        skipped_count += 1
                    if msg_id > max_seen_id:
                        max_seen_id = msg_id

                # Update configuration with updated sync timestamp and message ID
                cfg = load_config()
                now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cfg["telegram_last_sync"] = now_iso
                if max_seen_id > last_msg_id:
                    cfg["telegram_last_msg_id"] = max_seen_id
                save_config(cfg)

                summary_msg = f"Telegram senkronizasyonu tamamlandı. {enqueued_count} yeni kitap kuyruğa alındı, {skipped_count} atlandı."
                log_event(
                    "telegram",
                    "INFO",
                    summary_msg,
                    enqueued=enqueued_count,
                    skipped=skipped_count,
                )
                notify_ws(
                    "telegram_sync",
                    {
                        "status": "finished",
                        "enqueued_count": enqueued_count,
                        "skipped_count": skipped_count,
                        "last_sync": now_iso,
                        "message": summary_msg,
                    },
                )

                return {
                    "success": True,
                    "scanned_count": scanned_count,
                    "enqueued_count": enqueued_count,
                    "skipped_count": skipped_count,
                    "last_sync": now_iso,
                    "message": summary_msg,
                }

            except FloodWaitError as flood_err:
                wait_sec = flood_err.seconds
                if wait_sec <= 10:
                    log_event(
                        "telegram",
                        "WARNING",
                        f"Telegram FloodWait sınırı ({wait_sec}s). Bekleniyor...",
                    )
                    notify_ws(
                        "telegram_sync",
                        {
                            "status": "flood_wait",
                            "seconds": wait_sec,
                            "message": f"Telegram isteği sınırlandı. {wait_sec} saniye bekleniyor...",
                        },
                    )
                    await asyncio.sleep(wait_sec)
                err_msg = f"Telegram FloodWait sınırı aşıldı! Lütfen {wait_sec} saniye bekleyin."
                log_event("telegram", "WARNING", err_msg)
                notify_ws(
                    "telegram_sync",
                    {"status": "flood_wait", "seconds": wait_sec, "message": err_msg},
                )
                return {"success": False, "error": err_msg, "flood_wait": wait_sec}
            except Exception as e:
                err_msg = f"Telegram senkronizasyonunda beklenmedik hata: {str(e)}"
                log_event("telegram", "ERROR", err_msg)
                notify_ws("telegram_sync", {"status": "error", "message": err_msg})
                return {"success": False, "error": err_msg}

        finally:
            if max_seen_id > last_msg_id:
                try:
                    c = load_config()
                    if max_seen_id > int(c.get("telegram_last_msg_id", 0) or 0):
                        c["telegram_last_msg_id"] = max_seen_id
                        save_config(c)
                except Exception as save_err:
                    log_event(
                        "telegram",
                        "WARNING",
                        f"Telegram last_msg_id kaydedilemedi: {save_err}",
                    )
            self._is_syncing = False

    async def disconnect(self) -> dict:
        """Disconnect Telegram client, revoke session and remove session files."""
        async with self._lock:
            if self._client is not None:
                try:
                    await self._client.disconnect()
                except Exception as disc_err:
                    logger.debug("Error during client disconnect: %s", disc_err)
                self._client = None

            self._pending_auth = None
            self._is_syncing = False

            # Delete session files
            for ext in ("", "-journal"):
                fpath = f"{SESSION_FILE}{ext}"
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except OSError as rm_err:
                        logger.debug("Could not remove session file %s: %s", fpath, rm_err)

            # Clear telegram config keys if desired (preserve api_id/hash for convenience if user reconnects)
            cfg = load_config()
            cfg["telegram_last_sync"] = ""
            cfg["telegram_last_msg_id"] = 0
            save_config(cfg)

            log_event(
                "telegram",
                "INFO",
                "Telegram oturumu kapatıldı ve session dosyası silindi.",
            )
            notify_ws("telegram_status", {"authorized": False, "connected": False})

            return {
                "success": True,
                "message": "Telegram bağlantısı başarıyla kesildi.",
            }

    async def save_chat_target(self, chat_target: str) -> dict:
        """Update and persist the target chat/channel."""
        cfg = load_config()
        old_target = str(cfg.get("telegram_chat_id", "me")).strip()
        new_target = str(chat_target or "me").strip()
        cfg["telegram_chat_id"] = new_target
        if old_target != new_target:
            cfg["telegram_last_msg_id"] = 0
        await asyncio.to_thread(save_config, cfg)
        log_event("telegram", "INFO", f"Telegram hedef kanal güncellendi: {new_target}")
        return {"success": True, "chat_id": new_target}


# Global singleton instance
telegram_service = TelegramService()
