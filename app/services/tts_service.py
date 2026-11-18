"""Natural Turkish Neural TTS Service with Prosody Pre-Processing & Word-Boundary Timestamps.

Uses ``edge-tts`` neural voices (``tr-TR-EmelNeural`` & ``tr-TR-AhmetNeural``) with a dedicated
Turkish literary/academic prosody normalizer, millisecond word boundary extraction for 60fps
karaoke tracking, and a bounded on-disk MP3+JSON cache under ``veriler/tts_cache``.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
from typing import Any

from app.constants import DATA_DIR
from app.logger import log_event

TTS_CACHE_DIR = os.path.join(DATA_DIR, "tts_cache")
MAX_TTS_CACHE_ITEMS = 160

SUPPORTED_TURKISH_VOICES: dict[str, dict[str, str]] = {
    "tr-TR-EmelNeural": {
        "id": "tr-TR-EmelNeural",
        "label": "Emel (Doğal Stüdyo · Kadın)",
        "gender": "female",
        "lang": "tr-TR",
    },
    "tr-TR-AhmetNeural": {
        "id": "tr-TR-AhmetNeural",
        "label": "Ahmet (Doğal Stüdyo · Erkek)",
        "gender": "male",
        "lang": "tr-TR",
    },
    "en-US-AriaNeural": {
        "id": "en-US-AriaNeural",
        "label": "Aria (English Studio)",
        "gender": "female",
        "lang": "en-US",
    },
}

# Turkish literary & academic abbreviations expanded for natural breathing & prosody
_TR_ABBREV_EXPANSIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bProf\.\s*Dr\.", flags=re.I), "Profesör Doktor"),
    (re.compile(r"\bDoç\.\s*Dr\.", flags=re.I), "Doçent Doktor"),
    (re.compile(r"\bYrd\.\s*Doç\.", flags=re.I), "Yardımcı Doçent"),
    (re.compile(r"\bDr\.(?=\s+[A-ZÇĞİÖŞÜ])"), "Doktor"),
    (re.compile(r"\bHz\.(?=\s+[A-ZÇĞİÖŞÜ])"), "Hazreti"),
    (re.compile(r"\bbkz\.", flags=re.I), "bakınız"),
    (re.compile(r"\bvb\.", flags=re.I), "ve benzeri"),
    (re.compile(r"\bvs\.", flags=re.I), "vesaire"),
    (re.compile(r"\börn\.", flags=re.I), "örneğin"),
    (re.compile(r"\byy\.", flags=re.I), "yüzyıl"),
    (re.compile(r"\bÇev\.", flags=re.I), "Çeviren"),
    (re.compile(r"\bHaz\.", flags=re.I), "Hazırlayan"),
    (re.compile(r"\bM\.Ö\.", flags=re.I), "Milattan Önce"),
    (re.compile(r"\bM\.S\.", flags=re.I), "Milattan Sonra"),
    (re.compile(r"\bs\.\s*(\d+)"), r"sayfa \1"),
)


def normalize_turkish_prosody_text(raw_text: str) -> str:
    """Clean PDF hyphenation, footnote brackets, and abbreviations so Turkish TTS sounds warm and natural."""
    if not raw_text:
        return ""

    txt = raw_text.replace("\u00ad", "")
    # Join syllabified PDF line-break hyphens: "düşün-\ncenin" -> "düşüncenin"
    txt = re.sub(r"([a-zçğıöşüA-ZÇĞİÖŞÜ]{2,})-\s*\r?\n\s*([a-zçğıöşü]{2,})", r"\1\2", txt)
    # Remove isolated bracketed numeric footnote markers like [1], [24]
    txt = re.sub(r"\[\d{1,3}\]", " ", txt)
    # Collapse single line breaks inside paragraphs into spaces while preserving paragraph pauses
    txt = re.sub(r"\r?\n\s*\r?\n", ". ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()

    for pat, repl in _TR_ABBREV_EXPANSIONS:
        txt = pat.sub(repl, txt)

    return txt.strip()


def split_turkish_sentences(raw_text: str, max_sentence_chars: int = 320) -> list[str]:
    """Split page text into natural prosodic Turkish sentences without cutting ordinals or initials."""
    if not raw_text or not raw_text.strip():
        return []

    cleaned = raw_text.replace("\u00ad", "")
    cleaned = re.sub(
        r"([a-zçğıöşüA-ZÇĞİÖŞÜ]{2,})-\s*\r?\n\s*([a-zçğıöşü]{2,})", r"\1\2", cleaned
    )

    # Protect ordinals ("19. yüzyıl") and initials ("A. Hamdi") before sentence splitting
    protected = re.sub(r"(\b\d{1,4})\.\s+(?=[a-zçğıöşü])", r"\g<1>⟪ORD⟫ ", cleaned)
    protected = re.sub(r"\b([A-ZÇĞİÖŞÜ])\.\s+(?=[A-ZÇĞİÖŞÜ])", r"\g<1>⟪INI⟫ ", protected)
    for abbr in ("Prof", "Dr", "Doç", "bkz", "vb", "vs", "örn", "yy", "Çev", "Haz", "Av"):
        protected = re.sub(rf"\b({abbr})\.", r"\g<1>⟪ABR⟫", protected, flags=re.I)

    raw_parts = re.split(r"(?<=[.!?…])\s+|\r?\n\s*\r?\n", protected)
    sentences: list[str] = []

    for part in raw_parts:
        restored = (
            part.replace("⟪ORD⟫ ", ". ")
            .replace("⟪INI⟫ ", ". ")
            .replace("⟪ABR⟫", ".")
            .strip()
        )
        restored = re.sub(r"\s+", " ", restored)
        if len(restored) < 2:
            continue
        if len(restored) <= max_sentence_chars:
            sentences.append(restored)
        else:
            # Break extra-long clauses gently on semicolons / colons / em-dashes
            clauses = re.split(r"(?<=[;:—–])\s+", restored)
            buf = ""
            for cl in clauses:
                if buf and len(buf) + len(cl) + 1 > max_sentence_chars:
                    sentences.append(buf.strip())
                    buf = cl
                else:
                    buf = f"{buf} {cl}".strip() if buf else cl
            if buf.strip():
                sentences.append(buf.strip())

    return sentences


def _format_edge_rate(rate: float) -> str:
    """Convert numeric multiplier (e.g. 1.15) into edge-tts percentage string (e.g. '+15%')."""
    clamped = max(0.5, min(2.0, float(rate)))
    pct = int(round((clamped - 1.0) * 100))
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


def _estimate_word_timings(spoken_text: str, total_duration_ms: float) -> list[dict[str, Any]]:
    """Fallback proportional word-boundary estimator when provider omits granular word ticks."""
    tokens = [w for w in spoken_text.split() if w]
    if not tokens:
        return []
    dur = max(400.0, total_duration_ms)
    weights = [max(2, len(w)) for w in tokens]
    total_w = float(sum(weights))
    cursor = 0.0
    words: list[dict[str, Any]] = []
    for tok, w in zip(tokens, weights, strict=False):
        span = (w / total_w) * dur
        words.append(
            {
                "t": tok,
                "start_ms": round(cursor, 1),
                "end_ms": round(cursor + span, 1),
            }
        )
        cursor += span
    return words


def _prune_tts_cache() -> None:
    """Keep TTS disk cache bounded by removing oldest MP3/JSON pairs."""
    if not os.path.exists(TTS_CACHE_DIR):
        return
    try:
        mp3_files = [
            os.path.join(TTS_CACHE_DIR, f)
            for f in os.listdir(TTS_CACHE_DIR)
            if f.endswith(".mp3")
        ]
        if len(mp3_files) <= MAX_TTS_CACHE_ITEMS:
            return
        mp3_files.sort(key=os.path.getmtime, reverse=True)
        for stale_mp3 in mp3_files[MAX_TTS_CACHE_ITEMS:]:
            stem = stale_mp3[:-4]
            for ext in (".mp3", ".json"):
                target = stem + ext
                if os.path.exists(target):
                    try:
                        os.remove(target)
                    except OSError as rm_err:
                        log_event("system", "DEBUG", f"TTS cache prune note: {rm_err}")
    except Exception as err:
        log_event("system", "DEBUG", f"TTS cache cleanup check note: {err}")


class NeuralTTSService:
    """Synthesizes natural Turkish neural speech with cached MP3 audio and word timestamps."""

    def get_voices(self) -> list[dict[str, str]]:
        """Return available studio neural voices."""
        return list(SUPPORTED_TURKISH_VOICES.values())

    async def synthesize_sentence(
        self,
        raw_text: str,
        voice: str = "tr-TR-EmelNeural",
        rate: float = 1.0,
    ) -> dict[str, Any]:
        """Synthesize a sentence/paragraph to cached MP3 + word boundaries."""
        safe_voice = voice if voice in SUPPORTED_TURKISH_VOICES else "tr-TR-EmelNeural"
        spoken_text = normalize_turkish_prosody_text(raw_text)
        if not spoken_text:
            return {
                "available": False,
                "reason": "empty_text",
                "audio_key": "",
                "words": [],
                "duration_ms": 0.0,
            }

        rate_str = _format_edge_rate(rate)
        cache_key = hashlib.sha256(
            f"{safe_voice}|{rate_str}|{spoken_text}".encode()
        ).hexdigest()[:32]

        os.makedirs(TTS_CACHE_DIR, exist_ok=True)
        mp3_path = os.path.join(TTS_CACHE_DIR, f"{cache_key}.mp3")
        meta_path = os.path.join(TTS_CACHE_DIR, f"{cache_key}.json")

        if os.path.exists(mp3_path) and os.path.exists(meta_path) and os.path.getsize(mp3_path) > 128:
            try:
                with open(meta_path, encoding="utf-8") as mf:
                    meta = json.load(mf)
                return {
                    "available": True,
                    "cached": True,
                    "audio_key": cache_key,
                    "audio_url": f"/api/tts/audio/{cache_key}",
                    "voice": safe_voice,
                    "spoken_text": spoken_text,
                    "words": meta.get("words") or [],
                    "duration_ms": float(meta.get("duration_ms") or 0.0),
                }
            except Exception as rd_err:
                log_event("system", "DEBUG", f"TTS cache metadata read note: {rd_err}")

        try:
            import edge_tts  # type: ignore

            comm_kwargs: dict[str, Any] = {"rate": rate_str}
            sig = inspect.signature(edge_tts.Communicate)
            if "boundary" in sig.parameters:
                comm_kwargs["boundary"] = "WordBoundary"

            communicate = edge_tts.Communicate(spoken_text, safe_voice, **comm_kwargs)
            audio_chunks: list[bytes] = []
            words: list[dict[str, Any]] = []
            max_end_ms = 0.0

            async for chunk in communicate.stream():
                ctype = chunk.get("type")
                if ctype == "audio":
                    data_bytes = chunk.get("data")
                    if data_bytes:
                        audio_chunks.append(bytes(data_bytes))
                elif ctype in ("WordBoundary", "SentenceBoundary"):
                    w_txt = str(chunk.get("text") or "").strip()
                    offset_ms = round(float(chunk.get("offset") or 0.0) / 10000.0, 1)
                    dur_ms = round(float(chunk.get("duration") or 0.0) / 10000.0, 1)
                    end_ms = round(offset_ms + max(dur_ms, 55.0), 1)
                    if end_ms > max_end_ms:
                        max_end_ms = end_ms
                    if ctype == "WordBoundary" and w_txt:
                        words.append({"t": w_txt, "start_ms": offset_ms, "end_ms": end_ms})

            audio_bytes = b"".join(audio_chunks)
            if not audio_bytes:
                return {
                    "available": False,
                    "reason": "empty_audio",
                    "audio_key": "",
                    "words": [],
                    "duration_ms": 0.0,
                }

            if max_end_ms <= 0.0:
                # Approximate MP3 duration from 48kbps mono stream (~6 bytes/ms)
                max_end_ms = round(max(500.0, len(audio_bytes) / 6.0), 1)
            if not words:
                words = _estimate_word_timings(spoken_text, max_end_ms)

            with open(mp3_path, "wb") as af:
                af.write(audio_bytes)
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(
                    {
                        "voice": safe_voice,
                        "rate": rate_str,
                        "spoken_text": spoken_text,
                        "duration_ms": max_end_ms,
                        "words": words,
                    },
                    mf,
                    ensure_ascii=False,
                )

            _prune_tts_cache()
            return {
                "available": True,
                "cached": False,
                "audio_key": cache_key,
                "audio_url": f"/api/tts/audio/{cache_key}",
                "voice": safe_voice,
                "spoken_text": spoken_text,
                "words": words,
                "duration_ms": max_end_ms,
            }
        except Exception as tts_err:
            log_event("system", "WARNING", f"Sinirsel TTS sentez uyarısı: {tts_err}")
            return {
                "available": False,
                "reason": str(tts_err),
                "audio_key": "",
                "words": [],
                "duration_ms": 0.0,
            }


neural_tts_service = NeuralTTSService()
