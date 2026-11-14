"""Gemini Multi-Model Cascade Manager.

Coordinates hierarchical model execution across Gemini Flash variants:
1. gemini-3.8-flash (RPM: 5, RPD: 20, TPM: 210K) - Primary
2. gemini-3.7-flash (RPM: 5, RPD: 20, TPM: 210K) - Reasoning/Thinking Engine
3. gemini-3.6-flash (RPM: 5, RPD: 20, TPM: 210K) - Balanced Flagship
4. gemini-3.5-flash (RPM: 5, RPD: 20, TPM: 210K) - Stable Workhorse
5. gemini-3.5-flash-lite (RPM: 13, RPD: 1500, TPM: 210K) - High-Volume Safety Net
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.tasks import GeminiRateLimiter

logger = logging.getLogger(__name__)

# Default model definitions with their respective free-tier boundaries
DEFAULT_CASCADE_PROFILES = [
    {
        "model": "gemini-3.8-flash",
        "rpm": 5,
        "tpm": 210000,
        "rpd": 20,
        "tier": "primary",
    },
    {
        "model": "gemini-3.7-flash",
        "rpm": 5,
        "tpm": 210000,
        "rpd": 20,
        "tier": "reasoning",
    },
    {
        "model": "gemini-3.6-flash",
        "rpm": 5,
        "tpm": 210000,
        "rpd": 20,
        "tier": "balanced",
    },
    {
        "model": "gemini-3.5-flash",
        "rpm": 5,
        "tpm": 210000,
        "rpd": 20,
        "tier": "standard",
    },
    {
        "model": "gemini-3.5-flash-lite",
        "rpm": 13,
        "tpm": 210000,
        "rpd": 1500,
        "tier": "safety_net",
    },
]


class CascadeModelProfile:
    """Tracks rate limiting, daily quotas, and cooldowns for a specific Gemini model."""

    def __init__(
        self,
        model_name: str,
        rpm: int = 5,
        tpm: int = 210000,
        rpd: int = 20,
        tier: str = "standard",
    ):
        self.model_name = model_name
        self.rpm = rpm
        self.tpm = tpm
        self.rpd = rpd
        self.tier = tier
        self.rate_limiter = GeminiRateLimiter(rpm=rpm, tpm=tpm)
        self.daily_requests: int = 0
        self.last_day: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.cooldown_until: float = 0.0
        self.is_exhausted_today: bool = False
        self.last_error: str = ""

    def _check_and_reset_day(self) -> None:
        """Reset daily counter at midnight UTC."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self.last_day:
            self.daily_requests = 0
            self.last_day = today
            self.is_exhausted_today = False
            self.last_error = ""

    def is_available(self, estimated_tokens: int = 0) -> tuple[bool, str]:
        """Check if model can execute immediately without sleeping."""
        self._check_and_reset_day()
        now = time.time()

        if self.is_exhausted_today:
            return False, f"Günlük kota tükendi ({self.daily_requests}/{self.rpd} RPD)"

        if self.rpd > 0 and self.daily_requests >= self.rpd:
            self.is_exhausted_today = True
            return (
                False,
                f"Günlük kota sınırı aşıldı ({self.daily_requests}/{self.rpd} RPD)",
            )

        if now < self.cooldown_until:
            wait_sec = max(1, int(self.cooldown_until - now))
            return False, f"Geçici soğumada ({wait_sec}s kaldı: {self.last_error})"

        # Check sliding 60-second window
        with self.rate_limiter._lock:
            valid_history = [
                (t, tok) for t, tok in self.rate_limiter.request_history if now - t < 60.0
            ]
            self.rate_limiter.request_history = valid_history

            if len(valid_history) >= self.rpm:
                return (
                    False,
                    f"Dakikalık limit dolu ({len(valid_history)}/{self.rpm} RPM)",
                )

            curr_tpm = sum(tok for _, tok in valid_history)
            if (curr_tpm + estimated_tokens) > self.tpm:
                return (
                    False,
                    f"Dakikalık token yükü dolu ({curr_tpm}+{estimated_tokens}/{self.tpm} TPM)",
                )

        return True, "ok"

    def record_usage(self, estimated_tokens: int = 0) -> None:
        """Record successful invocation for rate limiter and daily stats."""
        self._check_and_reset_day()
        self.daily_requests += 1
        now = time.time()
        with self.rate_limiter._lock:
            self.rate_limiter.request_history.append((now, max(1, estimated_tokens)))

    def record_cooldown(self, seconds: float, reason: str = "") -> None:
        """Mark model temporarily unavailable for short cooldown period."""
        self.cooldown_until = time.time() + seconds
        self.last_error = reason

    def record_daily_exhaustion(self, reason: str = "") -> None:
        """Mark model exhausted for remainder of current UTC day."""
        self.is_exhausted_today = True
        self.last_error = reason

    def to_dict(self) -> dict[str, Any]:
        """Export status representation for UI display."""
        self._check_and_reset_day()
        now = time.time()
        avail, reason = self.is_available(0)
        return {
            "model": self.model_name,
            "rpm": self.rpm,
            "rpd": self.rpd,
            "daily_requests": self.daily_requests,
            "available": avail,
            "reason": reason,
            "is_exhausted_today": self.is_exhausted_today,
            "in_cooldown": now < self.cooldown_until,
            "cooldown_remaining": max(0, int(self.cooldown_until - now)),
            "tier": self.tier,
        }


class GeminiCascadeManager:
    """Manages the fallback priority chain across multiple Gemini models."""

    def __init__(self, profiles: list[dict[str, Any]] | None = None):
        defs = profiles or DEFAULT_CASCADE_PROFILES
        self.profiles: dict[str, CascadeModelProfile] = {
            p["model"]: CascadeModelProfile(
                model_name=p["model"],
                rpm=p.get("rpm", 5),
                tpm=p.get("tpm", 210000),
                rpd=p.get("rpd", 20),
                tier=p.get("tier", "standard"),
            )
            for p in defs
        }
        self.order: list[str] = [p["model"] for p in defs]

    def get_order(self) -> list[str]:
        return list(self.order)

    def set_order(self, new_order: list[str]) -> None:
        """Update model priority ordering."""
        valid = [m for m in new_order if m in self.profiles]
        for m in self.profiles:
            if m not in valid:
                valid.append(m)
        self.order = valid

    def _create_profile_for_model(self, m: str) -> CascadeModelProfile:
        is_lite = "flash-lite" in m.lower() or "lite" in m.lower()
        rpm = 13 if is_lite else 5
        rpd = 1500 if is_lite else 20
        tier = "safety_net" if is_lite else "standard"
        return CascadeModelProfile(model_name=m, rpm=rpm, tpm=210000, rpd=rpd, tier=tier)

    def _sanitize_model_chain_input(self, model_names: list[str] | None) -> list[str]:
        if not model_names or not isinstance(model_names, (list, tuple)):
            return [p["model"] for p in DEFAULT_CASCADE_PROFILES]
        valid = [m.strip() for m in model_names if isinstance(m, str) and m.strip()]
        return valid or [p["model"] for p in DEFAULT_CASCADE_PROFILES]

    def configure_chain(self, model_names: list[str] | None) -> None:
        """Configure active chain from user-defined model names list."""
        valid = self._sanitize_model_chain_input(model_names)
        for m in valid:
            if m not in self.profiles:
                self.profiles[m] = self._create_profile_for_model(m)
        self.order = valid

    def get_status_summary(self) -> list[dict[str, Any]]:
        """Return status for all models in order for UI/API."""
        return [self.profiles[m].to_dict() for m in self.order]

    def _prepare_model_attempt(
        self,
        idx: int,
        total_models: int,
        model_name: str,
        profile: CascadeModelProfile,
        estimated_tokens: int,
        task_id: str | None,
        log_fn: Callable[..., None],
    ) -> bool:
        """Check availability and wait on rate limiter if last safety net model."""
        avail, reason = profile.is_available(estimated_tokens)
        if not avail and idx < total_models - 1:
            next_model = self.order[idx + 1]
            log_fn(
                "DEBUG",
                f"[Model Zinciri] {idx + 1}. Model ({model_name}) meşgul ({reason}). Sıradaki {idx + 2}. Model ({next_model}) deneniyor...",
                model=model_name,
                next_model=next_model,
                task_id=task_id,
                reason=reason,
            )
            return False

        if not avail and idx == total_models - 1:
            log_fn(
                "INFO",
                f"[Model Zinciri] Tüm kademeler dolu. Son model ({model_name}) hız sınırını bekliyor...",
                model=model_name,
                task_id=task_id,
            )
            profile.rate_limiter.wait_if_needed(estimated_tokens=estimated_tokens, record=False)
        return True

    @staticmethod
    def _handle_model_error(
        err_str: str,
        idx: int,
        total_models: int,
        model_name: str,
        profile: CascadeModelProfile,
        task_id: str | None,
        log_fn: Callable[..., None],
    ) -> None:
        """Categorize error and adjust model cooldown or re-raise critical errors."""
        # Fast-fail on non-retryable credentials/arguments errors
        if any(
            code in err_str
            for code in [
                "401",
                "403",
                "API_KEY_INVALID",
                "PERMISSION_DENIED",
                "INVALID_ARGUMENT",
            ]
        ):
            log_fn(
                "ERROR",
                f"[Model Zinciri] Kritik yetki/parametre hatası, model zinciri sonlandırılıyor: {err_str[:150]}",
                model=model_name,
                task_id=task_id,
            )
            raise RuntimeError(f"Kritik API Hatası: {err_str}")

        # Check for 503 Server Overload
        if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
            profile.record_cooldown(120.0, "Google sunucu yoğunluğu (503)")
            log_fn(
                "WARNING",
                f"[Model Zinciri] {idx + 1}. Model ({model_name}) aşırı sunucu yoğunluğu bildirdi (503). Geçici soğumaya alındı, sıradaki modele devrediliyor...",
                model=model_name,
                task_id=task_id,
                error=err_str[:200],
            )
            return

        # Check for 429 Quota Exhaustion
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            if any(
                k in err_str.lower() for k in ("day", "limit: 0", "exceeded your current quota")
            ):
                profile.record_daily_exhaustion("Günlük kota tükendi (429)")
                log_fn(
                    "WARNING",
                    f"[Model Zinciri] {idx + 1}. Model ({model_name}) günlük kotası tükendi (429). Bugünlük devreden çıkarıldı, sıradaki modele devrediliyor...",
                    model=model_name,
                    task_id=task_id,
                    error=err_str[:200],
                )
            else:
                profile.record_cooldown(30.0, "Dakikalık hız limiti (429)")
                log_fn(
                    "WARNING",
                    f"[Model Zinciri] {idx + 1}. Model ({model_name}) dakikalık limitine takıldı (429). Sıradaki modele devrediliyor...",
                    model=model_name,
                    task_id=task_id,
                )
            return

        log_fn(
            "ERROR",
            f"[Model Zinciri] {idx + 1}. Model ({model_name}) beklenmeyen hata verdi: {err_str[:150]}",
            model=model_name,
            task_id=task_id,
        )
        if idx == total_models - 1:
            raise RuntimeError(err_str)

    def _create_cascade_logger(
        self, log_callback: Callable[..., None] | None
    ) -> Callable[..., None]:
        def _log(lvl: str, msg: str, **ctx) -> None:
            if log_callback:
                try:
                    log_callback("cascade", lvl, msg, **ctx)
                except TypeError:
                    try:
                        log_callback("cascade", lvl, msg, ctx)
                    except Exception as cb_err:
                        logger.debug("Cascade log callback failed: %s", cb_err)
                except Exception as cb_err:
                    logger.debug("Cascade log callback failed: %s", cb_err)
            logger.log(getattr(logging, lvl.upper(), logging.INFO), f"{msg} | {ctx}")

        return _log

    def _attempt_single_model_call(
        self,
        call_fn: Callable[[str], Any],
        model_name: str,
        profile: CascadeModelProfile,
        estimated_tokens: int,
        task_id: str | None,
        log_fn: Callable[..., None],
    ) -> Any:
        result = call_fn(model_name)
        if isinstance(result, str) and result.startswith("Error:"):
            raise RuntimeError(result)
        profile.record_usage(estimated_tokens)
        log_fn(
            "INFO",
            f"[Model Zinciri] Başarılı yanıt alındı ({model_name}).",
            model=model_name,
            task_id=task_id,
        )
        return result

    def execute_with_cascade(
        self,
        call_fn: Callable[[str], Any],
        estimated_tokens: int = 0,
        task_id: str | None = None,
        log_callback: Callable[[str, str, str, dict], None] | None = None,
    ) -> Any:
        """Execute an AI invocation through the cascade chain."""
        _log = self._create_cascade_logger(log_callback)
        errors = []
        total_models = len(self.order)

        for idx, model_name in enumerate(self.order):
            profile = self.profiles[model_name]
            should_run = self._prepare_model_attempt(
                idx, total_models, model_name, profile, estimated_tokens, task_id, _log
            )
            if not should_run:
                continue

            _log(
                "INFO",
                f"[Model Zinciri] {idx + 1}/{total_models}. Kademe ({model_name}) ile istek yapılıyor...",
                model=model_name,
                task_id=task_id,
                step=f"{idx + 1}/{total_models}",
            )

            try:
                return self._attempt_single_model_call(
                    call_fn, model_name, profile, estimated_tokens, task_id, _log
                )
            except Exception as e:
                err_str = str(e)
                errors.append(f"{model_name}: {err_str[:120]}")
                self._handle_model_error(
                    err_str, idx, total_models, model_name, profile, task_id, _log
                )

        # If all tried models failed
        raise RuntimeError(f"Tüm kademeli modeller tükendi veya hata verdi: {'; '.join(errors)}")


# Singleton instance shared across the application
cascade_manager = GeminiCascadeManager()
