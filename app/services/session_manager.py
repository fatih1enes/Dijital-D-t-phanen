"""In-memory stateful chat session manager for book workspaces.

Maintains Gemini chat sessions and conversation message history per book hash
during application runtime (cleared upon server restart).
"""

import asyncio
import threading
import time
from typing import Any

try:
    from google import genai
    from google.genai import types

    HAS_GOOGLE_GENAI = True
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore
    HAS_GOOGLE_GENAI = False
from app.logger import log_event


class BookSession:
    """Holds the active Gemini chat session, uploaded PDF handle, and message history."""

    def __init__(self, book_hash: str, pdf_path: str, model_name: str, system_instruction: str):
        self.book_hash = book_hash
        self.pdf_path = pdf_path
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.client: Any = None
        self.chat_session: Any = None
        self.uploaded_file: Any = None
        self.messages: list[dict[str, Any]] = []
        self.created_at: float = time.time()
        self.last_accessed: float = time.time()
        self.is_initialized: bool = False

    def is_expired(self, max_age_seconds: float = 144000) -> bool:
        """Check if Gemini File API upload is nearing expiration (default 40 hours, Google deletes at 48 hours)."""
        return (time.time() - self.created_at) > max_age_seconds

    def close(self) -> None:
        """Clean up uploaded file on Gemini cloud storage to free project storage quota."""
        if self.client and self.uploaded_file:
            try:
                file_name = getattr(self.uploaded_file, "name", None)
                if file_name:
                    self.client.files.delete(name=file_name)
                    log_event(
                        "ai_chat",
                        "INFO",
                        f"Gemini oturum dosyası buluttan temizlendi: {file_name}",
                        file_hash=self.book_hash,
                    )
            except Exception as e:
                log_event(
                    "ai_chat",
                    "WARNING",
                    f"Gemini dosyası silinirken hata: {e}",
                    file_hash=self.book_hash,
                )
            finally:
                self.uploaded_file = None
                self.chat_session = None
                self.is_initialized = False

    def _upload_book_file(self) -> Any:
        """Upload target book PDF to Gemini File API."""
        import os

        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"Kitap PDF dosyası bulunamadı: {self.pdf_path}")

        log_event(
            "ai_chat",
            "INFO",
            f"Kitap Gemini File API'ye yükleniyor (tek seferlik oturum): {self.pdf_path}",
            file_hash=self.book_hash,
        )
        return self.client.files.upload(file=self.pdf_path)

    def _build_initial_history(self) -> list:
        """Construct initial priming dialogue with uploaded document URI."""
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=self.uploaded_file.uri,
                        mime_type=self.uploaded_file.mime_type or "application/pdf",
                    ),
                    types.Part.from_text(
                        text="Bu kitabı baştan sona incele. Kitap ve konuları hakkında seninle doğal, akıcı bir şekilde sohbet edeceğiz."
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text="Kitabın tamamını dikkatle okudum ve inceledim. Tüm kavramlar, fikirler ve detaylar üzerine seninle sohbet etmeye hazırım."
                    )
                ],
            ),
        ]

    def _try_create_single_session(
        self, candidate_model: str, history: list, use_grounding: bool
    ) -> Any:
        config_kwargs: dict[str, Any] = {}
        if self.system_instruction:
            config_kwargs["system_instruction"] = self.system_instruction
        if use_grounding:
            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

        config: types.GenerateContentConfig | None
        try:
            config = types.GenerateContentConfig(**config_kwargs)
            return self.client.chats.create(model=candidate_model, config=config, history=history)
        except Exception as g_err:
            if not use_grounding:
                raise g_err
            config = (
                types.GenerateContentConfig(system_instruction=self.system_instruction)
                if self.system_instruction
                else None
            )
            return self.client.chats.create(model=candidate_model, config=config, history=history)

    def _create_chat_session_with_cascade(
        self, cascade_models: list[str], history: list, use_grounding: bool
    ) -> str:
        """Attempt to initialize a Gemini chat session across configured cascade models."""
        last_err = None
        for candidate_model in cascade_models:
            try:
                self.chat_session = self._try_create_single_session(
                    candidate_model, history, use_grounding
                )
                return candidate_model
            except Exception as e:
                last_err = e
                log_event(
                    "ai_chat",
                    "WARNING",
                    f"'{candidate_model}' ile kitap oturumu başlatılamadı ({e}), bir sonraki modele geçiliyor.",
                    file_hash=self.book_hash,
                )
                continue

        raise RuntimeError(f"Kitap sohbet oturumu oluşturulamadı: {last_err}")

    def initialize_session(self, api_key: str) -> None:
        """Initializes the Gemini client, uploads PDF once to Gemini File API, and starts chat."""
        if not HAS_GOOGLE_GENAI or genai is None:
            raise RuntimeError(
                "'google-genai' kütüphanesi sistemde bulunamadı. Lütfen 'pip install google-genai' çalıştırın."
            )

        if self.is_initialized and self.chat_session and not self.is_expired():
            return

        self.client = genai.Client(api_key=api_key)
        self.uploaded_file = self._upload_book_file()

        from app.config import load_config

        cfg = load_config()
        use_grounding = bool(cfg.get("google_search_grounding", False))
        history = self._build_initial_history()

        cascade_models = [self.model_name]
        if cfg.get("gemini_cascade_mode", True):
            from app.services.cascade_manager import cascade_manager

            cfg_models = cfg.get("gemini_cascade_models")
            if cfg_models and isinstance(cfg_models, list):
                cascade_manager.configure_chain(cfg_models)
            cascade_models = cascade_manager.get_order()

        try:
            active_model = self._create_chat_session_with_cascade(
                cascade_models, history, use_grounding
            )
            self.model_name = active_model
            self.is_initialized = True
            self.created_at = time.time()
            self.last_accessed = time.time()
            log_event(
                "ai_chat",
                "INFO",
                f"Kitap sohbet oturumu başarıyla oluşturuldu ve hazırlandı ({self.model_name}).",
                file_hash=self.book_hash,
            )
        except Exception:
            self.close()
            raise

    def send_user_message(self, user_text: str) -> str:
        """Sends a message to the existing Gemini chat session without re-uploading the PDF."""
        self.last_accessed = time.time()
        if not self.chat_session:
            raise RuntimeError("Sohbet oturumu başlatılmamış.")

        # Send directly to the active session first
        response = self.chat_session.send_message(user_text)
        reply_text = (
            response.text.strip()
            if response and hasattr(response, "text") and response.text
            else "Yanıt alınamadı."
        )

        # Record user message and assistant reply in history only after successful API call
        self.messages.append({"role": "user", "text": user_text, "timestamp": time.time()})
        self.messages.append({"role": "model", "text": reply_text, "timestamp": time.time()})

        return reply_text


class BookSessionManager:
    """Manages active book sessions in-memory with LRU and TTL eviction to prevent memory leaks."""

    def __init__(self, max_sessions: int = 20, ttl_seconds: float = 86400):
        self._sessions: dict[str, BookSession] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._state_lock = threading.Lock()
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds

    def _release_lock_if_free(self, book_hash: str) -> None:
        """Safely prune lock only if no coroutine currently holds or waits on it."""
        lock = self._locks.get(book_hash)
        if lock is not None and not lock.locked():
            self._locks.pop(book_hash, None)

    def lock_for(self, book_hash: str) -> asyncio.Lock:
        """Return an async lock specific to the book hash to serialize concurrent operations."""
        with self._state_lock:
            if book_hash not in self._locks:
                self._locks[book_hash] = asyncio.Lock()
            return self._locks[book_hash]

    def _evict_ttl_expired(self, now: float) -> None:
        with self._state_lock:
            stale_hashes = [
                h
                for h, sess in self._sessions.items()
                if (now - sess.last_accessed) > self.ttl_seconds or sess.is_expired()
            ]
            for h in stale_hashes:
                sess = self._sessions.pop(h, None)
                self._release_lock_if_free(h)
                if sess:
                    sess.close()

    def _evict_lru_excess(self) -> None:
        with self._state_lock:
            if len(self._sessions) <= self.max_sessions:
                return
            sorted_by_lru = sorted(self._sessions.items(), key=lambda kv: kv[1].last_accessed)
            excess_count = len(self._sessions) - self.max_sessions
            for h, _ in sorted_by_lru[:excess_count]:
                sess = self._sessions.pop(h, None)
                self._release_lock_if_free(h)
                if sess:
                    sess.close()

    def _evict_stale_sessions(self) -> None:
        """Evict sessions that have exceeded TTL or trim oldest when max_sessions is exceeded."""
        now = time.time()
        self._evict_ttl_expired(now)
        self._evict_lru_excess()

    def get_session(self, book_hash: str) -> BookSession | None:
        with self._state_lock:
            session = self._sessions.get(book_hash)
            if session:
                if (time.time() - session.last_accessed) > self.ttl_seconds or session.is_expired():
                    popped = self._sessions.pop(book_hash, None)
                    self._release_lock_if_free(book_hash)
                    if popped:
                        popped.close()
                    return None
                session.last_accessed = time.time()
            return session

    def get_or_create_session(
        self,
        book_hash: str,
        pdf_path: str,
        model_name: str,
        system_instruction: str,
        api_key: str,
    ) -> BookSession:
        self._evict_stale_sessions()
        session = self._sessions.get(book_hash)

        # If session exists, file matches, and hasn't expired, reuse it
        if (
            session
            and session.pdf_path == pdf_path
            and session.is_initialized
            and not session.is_expired()
        ):
            session.last_accessed = time.time()
            return session

        # Close and evict stale or path-mismatched session if it exists
        if session:
            popped = self._sessions.pop(book_hash, None)
            if popped:
                popped.close()

        # Create new session
        session = BookSession(
            book_hash=book_hash,
            pdf_path=pdf_path,
            model_name=model_name,
            system_instruction=system_instruction,
        )
        session.initialize_session(api_key=api_key)
        self._sessions[book_hash] = session
        return session

    def get_history(self, book_hash: str) -> list[dict[str, Any]]:
        session = self.get_session(book_hash)
        if not session:
            return []
        return session.messages

    def clear_session(self, book_hash: str) -> bool:
        with self._state_lock:
            session = self._sessions.pop(book_hash, None)
            self._release_lock_if_free(book_hash)
            if session:
                session.close()
                return True
            return False

    def close_all(self) -> None:
        """Clean up all active sessions and cloud files upon shutdown."""
        with self._state_lock:
            for sess in self._sessions.values():
                sess.close()
            self._sessions.clear()
            self._locks.clear()


# Global thread-safe session manager instance
book_session_manager = BookSessionManager()
