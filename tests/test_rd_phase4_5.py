"""Unit and integration tests for Faz 4 (Turkish Neural TTS & Karaoke) and Faz 5 (FSRS v5 & Reading Analytics)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest

import app.routers.tts as tts_router_mod
import app.services.tts_service as tts_mod
from app.main import app as fastapi_app
from app.services.fsrs_service import (
    STATE_RELEARNING,
    STATE_REVIEW,
    fsrs_scheduler,
    retrievability,
)
from app.services.tts_service import (
    normalize_turkish_prosody_text,
    split_turkish_sentences,
)


def test_turkish_prosody_normalizer_and_sentence_splitter() -> None:
    """Verify PDF hyphenation healing, Turkish abbreviation expansion, and ordinal-safe splitting."""
    raw_academic = (
        "Çağdaş düşün-\ncenin temelleri [14] Prof. Dr. Ahmet Hamdi tarafından "
        "s. 42 ve bkz. ekler M.Ö. 4. yy. bağlamında incelenmiştir."
    )
    normalized = normalize_turkish_prosody_text(raw_academic)
    assert "düşüncenin" in normalized
    assert "[14]" not in normalized
    assert "Profesör Doktor" in normalized
    assert "sayfa 42" in normalized
    assert "bakınız" in normalized
    assert "Milattan Önce" in normalized
    assert "yüzyıl" in normalized

    # Ordinals ("19. yüzyıl"), initials ("A. Hamdi"), and titles ("Prof. Dr.") must NOT split mid-sentence
    tricky_page = (
        "Prof. Dr. A. Hamdi Tanpınar 19. yüzyıl Türk edebiyatını derinlemesine incelemiştir. "
        "İkinci cümle burada başlar! Üçüncü soru cümlesi mi?"
    )
    sentences = split_turkish_sentences(tricky_page)
    assert len(sentences) == 3
    assert "19. yüzyıl" in sentences[0]
    assert "A. Hamdi" in sentences[0]
    assert sentences[1] == "İkinci cümle burada başlar!"
    assert sentences[2] == "Üçüncü soru cümlesi mi?"


@pytest.mark.asyncio
async def test_tts_endpoints_word_boundaries_and_disk_cache(tmp_path, monkeypatch) -> None:
    """Verify /api/tts/voices, /split-sentences, /synthesize WordBoundary timestamps, and MP3 disk cache."""
    cache_dir = str(tmp_path / "tts_cache_test")
    monkeypatch.setattr(tts_mod, "TTS_CACHE_DIR", cache_dir)
    monkeypatch.setattr(tts_router_mod, "TTS_CACHE_DIR", cache_dir)

    synth_call_count = 0
    fake_mp3_payload = b"ID3" + (b"\xff\xfb\x90\x64" * 80)

    class _FakeCommunicate:
        def __init__(self, text: str, voice: str, **kwargs: Any) -> None:
            self.text = text
            self.voice = voice
            self.kwargs = kwargs

        async def stream(self) -> AsyncIterator[dict[str, Any]]:
            nonlocal synth_call_count
            synth_call_count += 1
            yield {"type": "WordBoundary", "text": "Merhaba", "offset": 500_000, "duration": 2_800_000}
            yield {"type": "WordBoundary", "text": "dijital", "offset": 3_500_000, "duration": 3_100_000}
            yield {"type": "WordBoundary", "text": "kütüphane", "offset": 6_800_000, "duration": 4_200_000}
            yield {"type": "audio", "data": fake_mp3_payload}

    import edge_tts  # type: ignore

    monkeypatch.setattr(edge_tts, "Communicate", _FakeCommunicate)

    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        v_resp = await client.get("/api/tts/voices")
        assert v_resp.status_code == 200
        voice_ids = {v["id"] for v in v_resp.json()["voices"]}
        assert "tr-TR-EmelNeural" in voice_ids
        assert "tr-TR-AhmetNeural" in voice_ids

        sp_resp = await client.post(
            "/api/tts/split-sentences",
            json={"text": "Dr. Kemal 20. yüzyıl felsefesini anlattı. Dinleyiciler hayran kaldı."},
        )
        assert sp_resp.status_code == 200
        assert sp_resp.json()["count"] == 2

        # First synthesis -> calls Communicate.stream and writes MP3 + JSON to cache
        s1 = await client.post(
            "/api/tts/synthesize",
            json={"text": "Merhaba dijital kütüphane.", "voice": "tr-TR-EmelNeural", "rate": 1.0},
        )
        assert s1.status_code == 200
        d1 = s1.json()
        assert d1["available"] is True
        assert d1["cached"] is False
        assert synth_call_count == 1
        assert len(d1["words"]) == 3
        assert d1["words"][0]["t"] == "Merhaba"
        assert d1["words"][0]["start_ms"] == 50.0
        audio_key = d1["audio_key"]

        # Stream cached MP3 via /api/tts/audio/{audio_key}
        aud_resp = await client.get(f"/api/tts/audio/{audio_key}")
        assert aud_resp.status_code == 200
        assert aud_resp.headers["content-type"].startswith("audio/mpeg")
        assert aud_resp.content == fake_mp3_payload

        # Second synthesis with identical voice/rate/text -> instant disk cache hit!
        s2 = await client.post(
            "/api/tts/synthesize",
            json={"text": "Merhaba dijital kütüphane.", "voice": "tr-TR-EmelNeural", "rate": 1.0},
        )
        assert s2.status_code == 200
        assert s2.json()["cached"] is True
        assert synth_call_count == 1

        # Reject invalid audio_key path parameter
        bad_aud = await client.get("/api/tts/audio/invalid_key_traversal")
        assert bad_aud.status_code == 400


def test_fsrs_v5_memory_scheduler_invariants() -> None:
    """Verify FSRS v5 90% retrievability calibration, monotonic stability/difficulty, and lapse handling."""
    # Exact mathematical calibration of FSRS v5 power-law forgetting curve: R(S, S) == 0.90
    assert retrievability(0.0, 5.0) == pytest.approx(1.0)
    assert retrievability(5.0, 5.0) == pytest.approx(0.90, abs=1e-4)

    now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
    new_card: dict[str, Any] = {"durum": 0, "stability": 0.0, "difficulty": 5.0, "reps": 0, "lapses": 0}

    outcomes = [fsrs_scheduler.schedule(new_card, r, now=now) for r in (1, 2, 3, 4)]
    stabilities = [o["stability"] for o in outcomes]
    difficulties = [o["difficulty"] for o in outcomes]

    assert stabilities[0] < stabilities[1] < stabilities[2] < stabilities[3]
    assert difficulties[0] > difficulties[1] > difficulties[2] > difficulties[3]
    assert outcomes[2]["durum"] == STATE_REVIEW
    assert outcomes[2]["scheduled_days"] >= 1
    assert outcomes[3]["durum"] == STATE_REVIEW
    assert outcomes[3]["scheduled_days"] >= 4

    # Review card after 6 days: Good increases stability; Again triggers Relearning + lapse
    rev_card: dict[str, Any] = {
        "durum": STATE_REVIEW,
        "stability": 4.5,
        "difficulty": 5.2,
        "reps": 2,
        "lapses": 0,
        "last_review": (now - timedelta(days=6)).isoformat(),
    }
    good_rev = fsrs_scheduler.schedule(rev_card, 3, now=now)
    assert good_rev["durum"] == STATE_REVIEW
    assert good_rev["stability"] > 4.5

    lapse_rev = fsrs_scheduler.schedule(rev_card, 1, now=now)
    assert lapse_rev["durum"] == STATE_RELEARNING
    assert lapse_rev["lapses"] == 1
    assert lapse_rev["stability"] <= 4.5

    previews = fsrs_scheduler.preview_intervals(new_card, now=now)
    assert set(previews.keys()) == {"1", "2", "3", "4"}
    assert "dk" in previews["1"]
    assert "gün" in previews["4"]


@pytest.mark.asyncio
async def test_reading_analytics_and_srs_studio_endpoints(temp_db) -> None:
    """Verify reading heartbeat, 365d heatmap, ETA calculation, highlight-to-FSRS sync, and card grading."""
    b_hash = "f" * 64
    await temp_db.add_book(
        {
            "dosya_hash": b_hash,
            "dosya_yolu": "dummy_analytics.pdf",
            "dosya_adi": "dummy_analytics.pdf",
            "kitap_adi": "Epistemoloji ve Bellek",
            "yazar": "Henri Bergson",
            "sayfa_sayisi": 200,
        }
    )
    await temp_db.conn.execute(
        "UPDATE kitaplar SET okunulan_sayfa = 50, sayfa_sayisi = 200 WHERE dosya_hash = ?",
        (b_hash,),
    )
    await temp_db.conn.execute(
        """
        INSERT INTO kitap_notlari (id, dosya_hash, sayfa_no, secilen_metin, not_metni, renk_sinif, renk_hex)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "note-fsrs-1",
            b_hash,
            50,
            "Bilinç, geçmişi şimdiki zamana bağlayan kesintisiz bir süreklilik ve hafıza akışıdır.",
            "Bergson'da süre (durée) kavramının tanımı",
            "yellow",
            "#e8dca0",
        ),
    )
    await temp_db.conn.commit()

    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Record two focused reading heartbeats (total 360s = 6 min, 6 pages -> 60 pages/hour)
        hb1 = await client.post(
            "/api/analytics/heartbeat",
            json={"dosya_hash": b_hash, "delta_seconds": 180, "current_page": 53, "pages_read_delta": 3},
        )
        assert hb1.status_code == 200
        hb2 = await client.post(
            "/api/analytics/heartbeat",
            json={"dosya_hash": b_hash, "delta_seconds": 180, "current_page": 56, "pages_read_delta": 3},
        )
        assert hb2.status_code == 200

        # 2. Verify 365d heatmap, streak, velocity, and book completion ETA
        ana = await client.get("/api/analytics/reading")
        assert ana.status_code == 200
        adata = ana.json()
        assert adata["streak_days"] >= 1
        assert adata["today_minutes"] == 6
        assert len(adata["heatmap"]) == 365
        assert adata["heatmap"][-1]["level"] >= 1
        assert adata["pages_per_hour"] == pytest.approx(60.0, abs=1.0)
        eta_hashes = {b["dosya_hash"] for b in adata["eta_books"]}
        assert b_hash in eta_hashes

        # 3. Verify GET /api/srs/due auto-syncs highlight from kitap_notlari into FSRS deck
        due1 = await client.get("/api/srs/due")
        assert due1.status_code == 200
        ddata = due1.json()
        assert ddata["summary"]["due"] >= 1
        target_card = next(c for c in ddata["cards"] if c["not_id"] == "note-fsrs-1")
        assert "[ ……… ]" in target_card["on_yuz"]
        assert "intervals" in target_card

        # 4. Grade card with Good (3) -> moves to Review state, no longer due today
        rev = await client.post(
            f"/api/srs/cards/{target_card['id']}/review",
            json={"rating": 3},
        )
        assert rev.status_code == 200
        assert rev.json()["durum"] == STATE_REVIEW

        due2 = await client.get("/api/srs/due")
        assert due2.status_code == 200
        assert all(c["id"] != target_card["id"] for c in due2.json()["cards"])

        # 5. Custom card creation & deletion
        c_create = await client.post(
            "/api/srs/cards",
            json={
                "dosya_hash": b_hash,
                "sayfa_no": 12,
                "on_yuz": "Epistemoloji nedir?",
                "arka_yuz": "Bilginin doğasını, kaynağını ve sınırlarını inceleyen felsefe dalıdır.",
                "baglam": "Özel Not",
            },
        )
        assert c_create.status_code == 200
        custom_id = c_create.json()["id"]

        c_del = await client.delete(f"/api/srs/cards/{custom_id}")
        assert c_del.status_code == 200
        assert c_del.json()["deleted"] is True
