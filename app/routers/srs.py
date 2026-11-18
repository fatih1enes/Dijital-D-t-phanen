"""Router for Focused Reading Analytics (Heatmap, Streak, Velocity/ETA) & FSRS v5 Active Recall Studio."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import _ensure_authorized
from app.database import DatabaseManager
from app.dependencies import get_db
from app.models import ReadingHeartbeatRequest, SRSCardCreateRequest, SRSReviewRequest
from app.services.fsrs_service import fsrs_scheduler

router = APIRouter(prefix="/api", tags=["analytics-srs"])


async def _ensure_analytics_and_srs_tables(db: DatabaseManager) -> None:
    """Defensively ensure okuma_oturumlari and srs_kartlari exist on active connection."""
    if getattr(db.conn, "_has_srs_tables", False):
        return
    await db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS okuma_oturumlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_hash TEXT NOT NULL,
            tarih_gun TEXT NOT NULL,
            sure_saniye INTEGER NOT NULL DEFAULT 0,
            okunan_sayfa_sayisi INTEGER NOT NULL DEFAULT 0,
            baslangic_sayfa INTEGER DEFAULT 1,
            bitis_sayfa INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dosya_hash, tarih_gun)
        )
        """
    )
    await db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS srs_kartlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_hash TEXT NOT NULL,
            not_id TEXT,
            sayfa_no INTEGER DEFAULT 1,
            on_yuz TEXT NOT NULL,
            arka_yuz TEXT NOT NULL,
            baglam TEXT DEFAULT '',
            durum INTEGER DEFAULT 0,
            stability REAL DEFAULT 0.0,
            difficulty REAL DEFAULT 5.0,
            reps INTEGER DEFAULT 0,
            lapses INTEGER DEFAULT 0,
            scheduled_days INTEGER DEFAULT 0,
            elapsed_days INTEGER DEFAULT 0,
            last_review TEXT,
            due_at TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.conn._has_srs_tables = True  # type: ignore[attr-defined]


def _build_cloze_question(quote_text: str, note_text: str, book_title: str, page_no: int) -> tuple[str, str]:
    """Create an engaging active-recall front prompt and rich answer back from a highlight/note."""
    clean_quote = re.sub(r"\s+", " ", (quote_text or "")).strip()
    clean_note = re.sub(r"\s+", " ", (note_text or "")).strip()

    if clean_note and clean_quote:
        if clean_note.endswith("?"):
            return clean_note, f"«{clean_quote}»"
        # Use user's conceptual note as cue, recall exact passage & synthesis
        words = [w for w in clean_quote.split() if len(re.sub(r"\W+", "", w)) >= 5]
        if words and len(clean_quote) >= 35:
            target_w = max(words, key=len)
            masked = clean_quote.replace(target_w, "[ ……… ]", 1)
            front = f"{masked}\n\nİpucu Notu: {clean_note}"
        else:
            front = f"Bu not hangi temel argümanı özetliyor?\n«{clean_note}»"
        back = f"«{clean_quote}»\n\nNotunuz: {clean_note}"
        return front, back

    if clean_quote:
        words = [w for w in clean_quote.split() if len(re.sub(r"\W+", "", w)) >= 5]
        if words:
            target_w = words[len(words) // 2]
            masked = clean_quote.replace(target_w, "[ ……… ]", 1)
            return f"Boşluğu tamamlayın ({book_title}, s. {page_no}):\n\n«{masked}»", f"**{target_w}**\n\nTam Alıntı: «{clean_quote}»"
        return f"{book_title} (s. {page_no}) anahtar alıntısını hatırlayın:", f"«{clean_quote}»"

    return f"{book_title} (s. {page_no}) okuma notu:", clean_note or "—"


@router.post("/analytics/heartbeat")
async def record_reading_heartbeat(
    payload: ReadingHeartbeatRequest,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Record active focused reading seconds and page progression for today."""
    _ensure_authorized(request)
    await _ensure_analytics_and_srs_tables(db)

    today_str = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    await db.conn.execute(
        """
        INSERT INTO okuma_oturumlari (
            dosya_hash, tarih_gun, sure_saniye, okunan_sayfa_sayisi, baslangic_sayfa, bitis_sayfa, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(dosya_hash, tarih_gun) DO UPDATE SET
            sure_saniye = okuma_oturumlari.sure_saniye + excluded.sure_saniye,
            okunan_sayfa_sayisi = okuma_oturumlari.okunan_sayfa_sayisi + excluded.okunan_sayfa_sayisi,
            bitis_sayfa = excluded.bitis_sayfa,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            payload.dosya_hash,
            today_str,
            int(payload.delta_seconds),
            int(payload.pages_read_delta),
            int(payload.current_page),
            int(payload.current_page),
        ),
    )
    await db.conn.commit()
    return {"status": "recorded", "date": today_str}


@router.get("/analytics/reading")
async def get_reading_analytics(
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Return 365-day reading heatmap, streak, reading speed (pages/hour), and active book ETAs."""
    _ensure_authorized(request)
    await _ensure_analytics_and_srs_tables(db)

    local_now = datetime.now(timezone.utc).astimezone()
    today_date = local_now.date()
    start_365 = (today_date - timedelta(days=364)).strftime("%Y-%m-%d")

    cur = await db.conn.execute(
        """
        SELECT tarih_gun, SUM(sure_saniye) AS total_sec, SUM(okunan_sayfa_sayisi) AS total_pg
        FROM okuma_oturumlari
        WHERE tarih_gun >= ?
        GROUP BY tarih_gun
        ORDER BY tarih_gun ASC
        """,
        (start_365,),
    )
    day_map: dict[str, tuple[int, int]] = {}
    for d_str, sec_val, pg_val in await cur.fetchall():
        day_map[str(d_str)] = (int(sec_val or 0), int(pg_val or 0))

    heatmap: list[dict[str, Any]] = []
    total_sec_365 = 0
    total_pg_365 = 0
    week_sec = 0

    for offset in range(364, -1, -1):
        d_obj = today_date - timedelta(days=offset)
        ds = d_obj.strftime("%Y-%m-%d")
        sec, pgs = day_map.get(ds, (0, 0))
        total_sec_365 += sec
        total_pg_365 += pgs
        if offset < 7:
            week_sec += sec
        minutes = sec / 60.0
        if sec <= 0:
            lvl = 0
        elif minutes < 10:
            lvl = 1
        elif minutes < 25:
            lvl = 2
        elif minutes < 50:
            lvl = 3
        else:
            lvl = 4
        heatmap.append({"date": ds, "seconds": sec, "pages": pgs, "level": lvl})

    # Compute active streak (today or yesterday backwards)
    streak = 0
    probe = today_date
    if day_map.get(probe.strftime("%Y-%m-%d"), (0, 0))[0] <= 0:
        probe = today_date - timedelta(days=1)
    while day_map.get(probe.strftime("%Y-%m-%d"), (0, 0))[0] > 0:
        streak += 1
        probe = probe - timedelta(days=1)

    today_sec = day_map.get(today_date.strftime("%Y-%m-%d"), (0, 0))[0]
    if total_sec_365 >= 120 and total_pg_365 > 0:
        pages_per_hour = round(max(6.0, min(120.0, (total_pg_365 / (total_sec_365 / 3600.0)))), 1)
    else:
        pages_per_hour = 28.0  # Realistic scholarly baseline until empirical sessions accumulate

    # Estimate completion ETA for books currently in progress
    eta_books: list[dict[str, Any]] = []
    try:
        cur_b = await db.conn.execute(
            """
            SELECT dosya_hash, kitap_adi, yazar, okunulan_sayfa, sayfa_sayisi
            FROM kitaplar
            WHERE COALESCE(sayfa_sayisi, 0) > 0 AND COALESCE(okunulan_sayfa, 1) > 1
              AND okunulan_sayfa < sayfa_sayisi
            ORDER BY okunulan_sayfa * 1.0 / sayfa_sayisi DESC
            LIMIT 6
            """
        )
        for bh, btitle, bauth, cur_p, tot_p in await cur_b.fetchall():
            rem_pages = max(0, int(tot_p) - int(cur_p))
            eta_min = max(1, int(round((rem_pages / max(1.0, pages_per_hour)) * 60.0)))
            pct = min(99, max(1, int(round((int(cur_p) / int(tot_p)) * 100.0))))
            eta_books.append(
                {
                    "dosya_hash": bh,
                    "kitap_adi": btitle or "İsimsiz Eser",
                    "yazar": bauth or "",
                    "okunulan_sayfa": int(cur_p),
                    "sayfa_sayisi": int(tot_p),
                    "progress_pct": pct,
                    "remaining_pages": rem_pages,
                    "eta_minutes": eta_min,
                }
            )
    except Exception:
        eta_books = []

    return {
        "status": "success",
        "streak_days": streak,
        "today_minutes": int(round(today_sec / 60.0)),
        "week_minutes": int(round(week_sec / 60.0)),
        "total_hours": round(total_sec_365 / 3600.0, 1),
        "pages_per_hour": pages_per_hour,
        "heatmap": heatmap,
        "eta_books": eta_books,
    }


async def _sync_annotations_into_srs(db: DatabaseManager) -> int:
    """Import any unlinked highlights/notes from kitap_notlari into srs_kartlari."""
    await _ensure_analytics_and_srs_tables(db)
    now_iso = datetime.now(timezone.utc).isoformat()

    cur = await db.conn.execute(
        """
        SELECT n.id, n.dosya_hash, n.sayfa_no, n.secilen_metin, n.not_metni,
               COALESCE(k.kitap_adi, 'Kitap') AS kitap_adi
        FROM kitap_notlari n
        LEFT JOIN kitaplar k ON k.dosya_hash = n.dosya_hash
        LEFT JOIN srs_kartlari s ON s.not_id = n.id
        WHERE s.id IS NULL
          AND (LENGTH(TRIM(COALESCE(n.secilen_metin, ''))) >= 12 OR LENGTH(TRIM(COALESCE(n.not_metni, ''))) >= 5)
        """
    )
    rows = await cur.fetchall()
    if not rows:
        return 0

    to_insert: list[tuple[Any, ...]] = []
    for n_id, b_hash, p_no, sel_txt, note_txt, b_title in rows:
        front, back = _build_cloze_question(
            str(sel_txt or ""), str(note_txt or ""), str(b_title or "Kitap"), int(p_no or 1)
        )
        ctx = f"{b_title} · Sayfa {int(p_no or 1)}"
        to_insert.append((str(b_hash), str(n_id), int(p_no or 1), front, back, ctx, now_iso))

    await db.conn.executemany(
        """
        INSERT INTO srs_kartlari (dosya_hash, not_id, sayfa_no, on_yuz, arka_yuz, baglam, due_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        to_insert,
    )
    await db.conn.commit()
    return len(to_insert)


@router.post("/srs/sync-from-notes")
async def sync_srs_cards_from_notes(
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Manually trigger synchronization of book highlights and notes into FSRS flashcards."""
    _ensure_authorized(request)
    added = await _sync_annotations_into_srs(db)
    return {"status": "success", "added": added}


@router.get("/srs/due")
async def get_due_srs_cards(
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Sync highlights/notes and return due FSRS v5 flashcards with interval previews."""
    _ensure_authorized(request)
    await _sync_annotations_into_srs(db)

    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    cur_counts = await db.conn.execute(
        """
        SELECT
            COUNT(*) AS total_cnt,
            SUM(CASE WHEN due_at <= ? THEN 1 ELSE 0 END) AS due_cnt,
            SUM(CASE WHEN durum = 0 THEN 1 ELSE 0 END) AS new_cnt,
            SUM(CASE WHEN durum IN (1, 3) THEN 1 ELSE 0 END) AS learn_cnt,
            SUM(CASE WHEN durum = 2 THEN 1 ELSE 0 END) AS rev_cnt
        FROM srs_kartlari
        """,
        (now_iso,),
    )
    cnt_row = await cur_counts.fetchone()

    cur_due = await db.conn.execute(
        """
        SELECT s.*, COALESCE(k.kitap_adi, 'Kitap') AS kitap_adi
        FROM srs_kartlari s
        LEFT JOIN kitaplar k ON k.dosya_hash = s.dosya_hash
        WHERE s.due_at <= ?
        ORDER BY s.durum ASC, s.due_at ASC
        LIMIT 50
        """,
        (now_iso,),
    )
    cards: list[dict[str, Any]] = []
    for r in await cur_due.fetchall():
        c_dict = dict(r)
        c_dict["intervals"] = fsrs_scheduler.preview_intervals(c_dict, now=now_utc)
        cards.append(c_dict)

    return {
        "status": "success",
        "summary": {
            "total": int(cnt_row[0] or 0) if cnt_row else 0,
            "due": int(cnt_row[1] or 0) if cnt_row else 0,
            "new": int(cnt_row[2] or 0) if cnt_row else 0,
            "learning": int(cnt_row[3] or 0) if cnt_row else 0,
            "review": int(cnt_row[4] or 0) if cnt_row else 0,
        },
        "cards": cards,
    }


@router.post("/srs/cards")
async def create_custom_srs_card(
    payload: SRSCardCreateRequest,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Create a custom FSRS v5 flashcard."""
    _ensure_authorized(request)
    await _ensure_analytics_and_srs_tables(db)
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = await db.conn.execute(
        """
        INSERT INTO srs_kartlari (dosya_hash, not_id, sayfa_no, on_yuz, arka_yuz, baglam, due_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.dosya_hash,
            payload.not_id,
            payload.sayfa_no,
            payload.on_yuz.strip(),
            payload.arka_yuz.strip(),
            payload.baglam.strip(),
            now_iso,
        ),
    )
    await db.conn.commit()
    return {"status": "created", "id": cur.lastrowid}


@router.post("/srs/cards/{card_id}/review")
async def review_srs_card(
    card_id: int,
    payload: SRSReviewRequest,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Grade an FSRS v5 flashcard (1..4) and persist updated stability, difficulty, and due_at."""
    _ensure_authorized(request)
    await _ensure_analytics_and_srs_tables(db)

    cur = await db.conn.execute("SELECT * FROM srs_kartlari WHERE id = ?", (card_id,))
    row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Kart bulunamadı.")

    card = dict(row)
    updated = fsrs_scheduler.schedule(card, payload.rating)
    await db.conn.execute(
        """
        UPDATE srs_kartlari
        SET durum = ?, stability = ?, difficulty = ?, reps = ?, lapses = ?,
            scheduled_days = ?, elapsed_days = ?, last_review = ?, due_at = ?
        WHERE id = ?
        """,
        (
            updated["durum"],
            updated["stability"],
            updated["difficulty"],
            updated["reps"],
            updated["lapses"],
            updated["scheduled_days"],
            updated["elapsed_days"],
            updated["last_review"],
            updated["due_at"],
            card_id,
        ),
    )
    await db.conn.commit()
    return {"status": "reviewed", "card_id": card_id, **updated}


@router.delete("/srs/cards/{card_id}")
async def delete_srs_card(
    card_id: int,
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> dict[str, Any]:
    """Delete an FSRS flashcard."""
    _ensure_authorized(request)
    await _ensure_analytics_and_srs_tables(db)
    cur = await db.conn.execute("DELETE FROM srs_kartlari WHERE id = ?", (card_id,))
    await db.conn.commit()
    return {"status": "deleted", "deleted": bool(cur.rowcount and cur.rowcount > 0)}
