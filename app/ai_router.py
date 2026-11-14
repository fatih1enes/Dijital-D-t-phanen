"""AI Router thin compatibility wrapper delegating core operations to AIService."""

from app.services.ai_service import AIService

# Thread-safe global instance of AIService for static backward-compatibility calls
_ai_service = AIService()


def generate_ai_response(
    prompt: str,
    provider: str,
    api_key: str,
    model: str | None = None,
    base_url: str | None = None,
    system_instruction: str | None = None,
    google_search_grounding: bool = False,
    pdf_path: str | None = None,
) -> str:
    """Compatibility function delegating to AIService."""
    return _ai_service.generate_text(
        prompt,
        provider,
        api_key,
        model,
        base_url,
        system_instruction,
        google_search_grounding,
        pdf_path,
    )
