# cspell:disable
"""AI Service managing text generation and embedding generations from various AI providers."""

import logging
import os
from typing import Any

from app.constants import DEFAULT_GEMINI_MODEL

logger = logging.getLogger(__name__)
try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    HAS_GOOGLE_GENAI = True
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore
    HAS_GOOGLE_GENAI = False


def _safe_log(cat: str, lvl: str, msg: str, **ctx: Any) -> None:
    try:
        from app.logger import log_event
        from app.utils import mask_sensitive_data

        sanitized_msg = mask_sensitive_data(msg)
        sanitized_ctx = {
            k: (mask_sensitive_data(str(v)) if isinstance(v, (str, Exception)) else v)
            for k, v in ctx.items()
        }
        log_event(cat, lvl, sanitized_msg, **sanitized_ctx)
    except Exception as log_err:
        logger.debug("Fallback safe log error: %s", log_err)


class AIService:
    """Service handling third-party AI provider calls (Text Generation and Embeddings)."""

    def _resolve_api_key(self, provider: str, api_key: str) -> str:
        from app.config import is_real_api_key, load_config

        if is_real_api_key(api_key) or provider in ["ollama", "lmstudio"]:
            return api_key
        cfg = load_config()
        cfg_k = str(cfg.get("ai_api_key") or "").strip()
        return (
            cfg_k if is_real_api_key(cfg_k) else str(os.environ.get("GEMINI_API_KEY") or "").strip()
        )

    def _upload_pdf(self, client: Any, pdf_path: str | None) -> Any:
        if pdf_path and os.path.exists(pdf_path):
            try:
                return client.files.upload(file=pdf_path)
            except Exception as e:
                _safe_log("ai_analyze", "WARNING", f"PDF yükleme başarısız: {e}", error=str(e))
        return None

    def _try_gemini_grounding(
        self,
        client: Any,
        target_model: str,
        prompt: str,
        uploaded_file: Any,
        system_instruction: str | None,
    ) -> str | None:
        try:
            cfg_content = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
            cnts = [uploaded_file, prompt] if uploaded_file else [prompt]
            resp = client.models.generate_content(
                model=target_model, contents=cnts, config=cfg_content
            )
            if resp and resp.candidates:
                try:
                    t = resp.text.strip()
                    if t:
                        _safe_log(
                            "ai_raw",
                            "INFO",
                            f"Gemini Grounding yanıtı alındı ({len(t)} karakter) [{target_model}]",
                            model=target_model,
                            preview=t[:1500],
                        )
                        return t
                except (AttributeError, ValueError) as ve:
                    logger.debug("Grounding text candidate extraction failed: %s", ve)
        except Exception as e:
            _safe_log(
                "ai_analyze",
                "WARNING",
                f"Model {target_model} ile Grounding başarısız oldu ({e}). Standart API'ye dönülüyor...",
                error=str(e),
                model=target_model,
            )
        return None

    def _extract_gemini_response_text(self, resp: Any, target_model: str) -> str:
        if not resp or not resp.candidates:
            err = f"Error: Gemini ({target_model}) returned an empty response (blocked or no candidates)."
            _safe_log("ai_analyze", "ERROR", err, model=target_model)
            return err

        try:
            t = resp.text.strip()
            _safe_log(
                "ai_raw",
                "INFO",
                f"Gemini yanıtı alındı ({len(t)} karakter) [{target_model}]",
                model=target_model,
                preview=t[:1500],
            )
            return t
        except (AttributeError, ValueError):
            if resp.candidates and resp.candidates[0].finish_reason:
                err = f"Error: Gemini blocked response. Reason: {resp.candidates[0].finish_reason}"
                _safe_log("ai_analyze", "ERROR", err, model=target_model)
                return err
            err = f"Error: Could not extract text from Gemini response ({target_model})."
            _safe_log("ai_analyze", "ERROR", err, model=target_model)
            return err

    def _execute_gemini_single_call(
        self,
        client: Any,
        target_model: str,
        prompt: str,
        uploaded_file: Any,
        system_instruction: str | None,
        google_search_grounding: bool,
    ) -> str:
        _safe_log(
            "ai_analyze",
            "INFO",
            f"Gemini API çağrısı başlatıldı ({target_model})",
            model=target_model,
            prompt_chars=len(prompt),
        )

        if google_search_grounding:
            grounded = self._try_gemini_grounding(
                client, target_model, prompt, uploaded_file, system_instruction
            )
            if grounded:
                return grounded

        cfg_content = (
            types.GenerateContentConfig(system_instruction=system_instruction)
            if system_instruction
            else None
        )

        cnts = [uploaded_file, prompt] if uploaded_file else [prompt]
        resp = client.models.generate_content(model=target_model, contents=cnts, config=cfg_content)
        return self._extract_gemini_response_text(resp, target_model)

    def _generate_gemini(
        self,
        prompt: str,
        api_key: str,
        model: str | None,
        system_instruction: str | None,
        google_search_grounding: bool,
        pdf_path: str | None,
    ) -> str:
        if not HAS_GOOGLE_GENAI:
            return "Hata: 'google-genai' kütüphanesi sisteminizde bulunamadı. Lütfen 'pip install google-genai' çalıştırın."
        client = genai.Client(api_key=api_key)

        from app.config import load_config

        cfg = load_config()
        cascade_mode = bool(cfg.get("gemini_cascade_mode", True))
        uploaded_file = self._upload_pdf(client, pdf_path)
        try:

            def _execute_single_call(target_model: str) -> str:
                return self._execute_gemini_single_call(
                    client,
                    target_model,
                    prompt,
                    uploaded_file,
                    system_instruction,
                    google_search_grounding,
                )

            if not cascade_mode:
                target = model or DEFAULT_GEMINI_MODEL
                return _execute_single_call(target)

            from app.services.cascade_manager import cascade_manager

            cfg_models = cfg.get("gemini_cascade_models")
            if cfg_models and isinstance(cfg_models, list):
                cascade_manager.configure_chain(cfg_models)
            est_tokens = max(1, int(len(prompt) / 3.0))
            return cascade_manager.execute_with_cascade(
                call_fn=_execute_single_call,
                estimated_tokens=est_tokens,
                log_callback=_safe_log,
            )
        finally:
            if uploaded_file and hasattr(uploaded_file, "name"):
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception as del_err:
                    _safe_log(
                        "ai_analyze",
                        "DEBUG",
                        f"Bulut dosya temizleme uyarısı: {del_err}",
                    )

    def _generate_local(
        self,
        provider: str,
        prompt: str,
        model: str | None,
        base_url: str | None,
        system_instruction: str | None,
    ) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return "Error: 'openai' library is not installed. Run 'pip install openai' to use local providers."

        default_url = (
            "http://localhost:11434/v1" if provider == "ollama" else "http://localhost:1234/v1"
        )
        url = (base_url or default_url).strip()
        if not url.startswith(("http://", "https://")) or "169.254.169.254" in url:
            return "Error: Invalid or blocked AI base URL."
        default_model = "gemma2" if provider == "ollama" else "model-identifier"
        model_name = model or default_model
        display_name = "Ollama" if provider == "ollama" else "LM Studio"

        _safe_log(
            "ai_analyze",
            "INFO",
            f"{display_name} API çağrısı başlatıldı ({model_name})",
            model=model_name,
            url=url,
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        client = OpenAI(base_url=url, api_key="local", timeout=60.0)
        response = client.chat.completions.create(model=model_name, messages=messages, timeout=60.0)
        if not response or not getattr(response, "choices", None):
            return f"Error: {display_name} returned an empty choices list."
        raw_content = getattr(response.choices[0].message, "content", None)
        if not raw_content:
            return f"Error: {display_name} returned empty message content."
        txt = str(raw_content).strip()
        _safe_log(
            "ai_raw",
            "INFO",
            f"{display_name} yanıtı alındı ({len(txt)} karakter)",
            model=model_name,
            preview=txt[:1500],
        )
        return txt

    def generate_text(
        self,
        prompt: str,
        provider: str,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        system_instruction: str | None = None,
        google_search_grounding: bool = False,
        pdf_path: str | None = None,
    ) -> str:
        """Route generation requests to different AI providers dynamically."""
        provider = provider.lower()
        api_key = self._resolve_api_key(provider, api_key)

        if not api_key and provider not in ["ollama", "lmstudio"]:
            return "Error: API Key is missing."

        try:
            if provider == "gemini":
                return self._generate_gemini(
                    prompt,
                    api_key,
                    model,
                    system_instruction,
                    google_search_grounding,
                    pdf_path,
                )
            if provider in ["ollama", "lmstudio"]:
                return self._generate_local(provider, prompt, model, base_url, system_instruction)
            return f"Error: Unsupported provider '{provider}'"
        except Exception as e:
            from app.utils import mask_sensitive_data

            clean_err = mask_sensitive_data(str(e))
            return f"Error from {provider.capitalize()}: {clean_err}"
