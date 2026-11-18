"""Router for Natural Turkish Studio Neural TTS & Karaoke Word Boundary Streaming."""

from __future__ import annotations

import os
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.auth import _ensure_authorized
from app.models import TTSSynthesizeRequest
from app.services.tts_service import (
    TTS_CACHE_DIR,
    neural_tts_service,
    split_turkish_sentences,
)

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSSentenceSplitRequest(BaseModel):
    """Request model for splitting raw page text into prosody-aware Turkish sentences."""

    text: str = Field(..., min_length=1, max_length=30000)


@router.get("/voices")
async def list_tts_voices(request: Request) -> dict[str, Any]:
    """Return available natural neural TTS voices."""
    _ensure_authorized(request)
    return {"status": "success", "voices": neural_tts_service.get_voices()}


@router.post("/split-sentences")
async def split_page_sentences(
    payload: TTSSentenceSplitRequest, request: Request
) -> dict[str, Any]:
    """Split raw PDF/EPUB page text into Turkish abbreviation-safe sentences."""
    _ensure_authorized(request)
    sentences = split_turkish_sentences(payload.text)
    return {"status": "success", "sentences": sentences, "count": len(sentences)}


@router.post("/synthesize")
async def synthesize_neural_tts(
    payload: TTSSynthesizeRequest, request: Request
) -> dict[str, Any]:
    """Synthesize a sentence into cached MP3 audio and millisecond word boundaries."""
    _ensure_authorized(request)
    return await neural_tts_service.synthesize_sentence(
        raw_text=payload.text,
        voice=payload.voice,
        rate=payload.rate,
    )


@router.get("/audio/{audio_key}")
async def serve_tts_audio(audio_key: str, request: Request) -> FileResponse:
    """Stream a cached neural TTS MP3 segment with Range support."""
    _ensure_authorized(request)
    if not re.fullmatch(r"[a-f0-9]{32}", audio_key):
        raise HTTPException(status_code=400, detail="Geçersiz ses anahtarı.")
    mp3_path = os.path.join(TTS_CACHE_DIR, f"{audio_key}.mp3")
    if not os.path.isfile(mp3_path):
        raise HTTPException(status_code=404, detail="Ses kaydı önbellekte bulunamadı.")
    return FileResponse(
        mp3_path,
        media_type="audio/mpeg",
        headers={"Cache-Control": "private, max-age=86400"},
    )
