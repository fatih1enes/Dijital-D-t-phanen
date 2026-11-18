"""19-Parameter FSRS v5 Spaced Repetition Memory Scheduler.

Implements the Free Spaced Repetition Scheduler v5 equations (Three-Component Model of Memory:
Retrievability R, Stability S, Difficulty D) for active recall of book highlights and notes.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

# Official FSRS v5 default 19-parameter weight vector
W_FSRS_V5: tuple[float, ...] = (
    0.40255,
    1.18385,
    3.17300,
    15.69105,
    7.19490,
    0.53450,
    1.46040,
    0.00460,
    1.54575,
    0.11920,
    1.01925,
    1.93950,
    0.11000,
    0.29605,
    2.26980,
    0.23150,
    2.98980,
    0.51655,
    0.66210,
)

DECAY = -0.5
FACTOR = 19.0 / 81.0
DESIRED_RETENTION = 0.90

STATE_NEW = 0
STATE_LEARNING = 1
STATE_REVIEW = 2
STATE_RELEARNING = 3


def _clamp(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))


def _initial_stability(rating: int, w: tuple[float, ...] = W_FSRS_V5) -> float:
    idx = max(0, min(3, int(rating) - 1))
    return max(0.1, float(w[idx]))


def _initial_difficulty(rating: int, w: tuple[float, ...] = W_FSRS_V5) -> float:
    g = float(_clamp(rating, 1, 4))
    d0 = w[4] - math.exp(w[5] * (g - 1.0)) + 1.0
    return _clamp(d0, 1.0, 10.0)


def _next_difficulty(cur_d: float, rating: int, w: tuple[float, ...] = W_FSRS_V5) -> float:
    g = float(_clamp(rating, 1, 4))
    delta_d = -w[6] * (g - 3.0)
    # FSRS v5 linear damping + mean reversion toward D0(4)
    d_prime = cur_d + delta_d * ((10.0 - cur_d) / 9.0)
    d0_easy = _initial_difficulty(4, w)
    merged = w[7] * d0_easy + (1.0 - w[7]) * d_prime
    return _clamp(merged, 1.0, 10.0)


def retrievability(elapsed_days: float, stability: float) -> float:
    """Compute FSRS v5 power-law retrievability R(t, S)."""
    s = max(0.05, float(stability))
    t = max(0.0, float(elapsed_days))
    return float((1.0 + FACTOR * (t / s)) ** DECAY)


def _next_recall_stability(
    d: float,
    s: float,
    r: float,
    rating: int,
    w: tuple[float, ...] = W_FSRS_V5,
) -> float:
    hard_penalty = w[15] if rating == 2 else 1.0
    easy_bonus = w[16] if rating == 4 else 1.0
    inc = (
        math.exp(w[8])
        * (11.0 - d)
        * (max(0.05, s) ** (-w[9]))
        * (math.exp((1.0 - r) * w[10]) - 1.0)
        * hard_penalty
        * easy_bonus
    )
    return max(0.1, s * (1.0 + inc))


def _next_forget_stability(
    d: float,
    s: float,
    r: float,
    w: tuple[float, ...] = W_FSRS_V5,
) -> float:
    s_f = (
        w[11]
        * (max(1.0, d) ** (-w[12]))
        * (((max(0.05, s) + 1.0) ** w[13]) - 1.0)
        * math.exp((1.0 - r) * w[14])
    )
    return max(0.1, min(s, s_f))


def _short_term_stability(s: float, rating: int, w: tuple[float, ...] = W_FSRS_V5) -> float:
    return max(0.1, s * math.exp(w[17] * (float(rating) - 3.0 + w[18])))


def _stability_to_interval_days(s: float, desired_r: float = DESIRED_RETENTION) -> int:
    raw = (s / FACTOR) * ((desired_r ** (1.0 / DECAY)) - 1.0)
    return max(1, min(3650, int(round(raw))))


def _parse_iso_utc(ts_str: str | None, fallback: datetime) -> datetime:
    if not ts_str:
        return fallback
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return fallback


class FSRSScheduler:
    """Stateless FSRS v5 scheduling engine for flashcard states and interval previews."""

    def schedule(
        self,
        card: dict[str, Any],
        rating: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Compute next FSRS v5 memory state for ``rating`` in {1: Again, 2: Hard, 3: Good, 4: Easy}."""
        g = int(_clamp(rating, 1, 4))
        now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)

        state = int(card.get("durum") or STATE_NEW)
        cur_s = float(card.get("stability") or 0.0)
        cur_d = float(card.get("difficulty") or 5.0)
        reps = int(card.get("reps") or 0) + 1
        lapses = int(card.get("lapses") or 0)

        last_rev = _parse_iso_utc(card.get("last_review"), now_utc)
        elapsed_days = (
            0.0
            if state == STATE_NEW or not card.get("last_review")
            else max(0.0, (now_utc - last_rev).total_seconds() / 86400.0)
        )

        if state == STATE_NEW or cur_s <= 0.0:
            new_d = _initial_difficulty(g)
            new_s = _initial_stability(g)
            if g == 1:
                next_state = STATE_LEARNING
                sched_days = 0
                due_dt = now_utc + timedelta(minutes=5)
                label = "5 dk"
            elif g == 2:
                next_state = STATE_LEARNING
                sched_days = 0
                due_dt = now_utc + timedelta(minutes=15)
                label = "15 dk"
            elif g == 3:
                next_state = STATE_REVIEW
                sched_days = max(1, _stability_to_interval_days(new_s))
                due_dt = now_utc + timedelta(days=sched_days)
                label = f"{sched_days} gün"
            else:
                next_state = STATE_REVIEW
                sched_days = max(4, _stability_to_interval_days(new_s))
                due_dt = now_utc + timedelta(days=sched_days)
                label = f"{sched_days} gün"
        elif state in (STATE_LEARNING, STATE_RELEARNING):
            new_d = _next_difficulty(cur_d, g)
            new_s = _short_term_stability(cur_s, g)
            if g == 1:
                next_state = state
                sched_days = 0
                due_dt = now_utc + timedelta(minutes=5)
                label = "5 dk"
            elif g == 2:
                next_state = state
                sched_days = 0
                due_dt = now_utc + timedelta(minutes=20)
                label = "20 dk"
            elif g == 3:
                next_state = STATE_REVIEW
                sched_days = max(1, _stability_to_interval_days(new_s))
                due_dt = now_utc + timedelta(days=sched_days)
                label = f"{sched_days} gün"
            else:
                next_state = STATE_REVIEW
                sched_days = max(3, _stability_to_interval_days(new_s * 1.35))
                due_dt = now_utc + timedelta(days=sched_days)
                label = f"{sched_days} gün"
        else:
            # STATE_REVIEW
            r_now = retrievability(max(0.1, elapsed_days), cur_s)
            new_d = _next_difficulty(cur_d, g)
            if g == 1:
                lapses += 1
                new_s = _next_forget_stability(new_d, cur_s, r_now)
                next_state = STATE_RELEARNING
                sched_days = 0
                due_dt = now_utc + timedelta(minutes=10)
                label = "10 dk"
            else:
                new_s = _next_recall_stability(new_d, cur_s, r_now, g)
                next_state = STATE_REVIEW
                raw_days = _stability_to_interval_days(new_s)
                if g == 2:
                    sched_days = max(1, raw_days)
                elif g == 3:
                    sched_days = max(2, raw_days)
                else:
                    sched_days = max(4, raw_days)
                due_dt = now_utc + timedelta(days=sched_days)
                label = f"{sched_days} gün"

        return {
            "durum": next_state,
            "stability": round(new_s, 4),
            "difficulty": round(new_d, 4),
            "reps": reps,
            "lapses": lapses,
            "scheduled_days": int(sched_days),
            "elapsed_days": int(round(elapsed_days)),
            "last_review": now_utc.isoformat(),
            "due_at": due_dt.isoformat(),
            "interval_label": label,
        }

    def preview_intervals(
        self, card: dict[str, Any], now: datetime | None = None
    ) -> dict[str, str]:
        """Return Turkish interval labels for all 4 FSRS ratings ('1'..'4')."""
        now_utc = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
        out: dict[str, str] = {}
        for r in (1, 2, 3, 4):
            sim = self.schedule(card, r, now=now_utc)
            out[str(r)] = str(sim["interval_label"])
        return out


fsrs_scheduler = FSRSScheduler()
