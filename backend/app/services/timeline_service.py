"""Confidence Timeline + Explain Decision (Sprint 6 spec).

Every `/api/ai/*` call already persists a decision to `ai_analysis`
(`app/services/ai_repository.py`), and since Sprint 6 that row also
carries the per-factor scores (`factors`) and human-readable reasons
(`reasons`) the Decision Engine computed for it — see
`app/models/ai_analysis.py`. This module never re-derives or re-scores
anything: it reads that real, already-persisted history and diffs
adjacent rows to answer "what changed and why."

A single `/api/assets/{symbol}/timeline` endpoint backs both the
Confidence Timeline widget and the "Why did AI change its mind?" modal —
the modal just renders more fields off the same React Query-cached entry
the widget already fetched, rather than a second endpoint/request for
data that's already in hand (see `backend/README.md`'s Asset Intelligence
Dashboard 2.0 section for why `/decision-history` wasn't shipped as a
separate route).

Rows written before this column existed have `factors`/`reasons` of
`None` — the timeline reports `AWAITING_DATA` for those honestly instead
of fabricating a retroactive explanation.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.services.ai_repository import get_recent_analysis

TIMELINE_LIMIT = 30
SCORE_CHANGE_THRESHOLD = 3.0
CONFIDENCE_CHANGE_THRESHOLD = 3.0
FACTOR_CHANGE_THRESHOLD = 5.0

FACTOR_LABELS: dict[str, str] = {
    "trend": "Trend",
    "momentum": "Momentum",
    "structure": "Structure",
    "oi": "Open Interest",
    "volume": "Volume",
    "funding": "Funding Rate",
    "volatility": "Volatility",
    "macro": "Macro",
    "news": "News",
    "whales": "Whale Activity",
}

TimelineDataStatus = Literal["OK", "AWAITING_DATA"]


@dataclass(frozen=True)
class TimelineEntry:
    time: int
    score: float
    confidence: float
    direction: str
    change_summary: str | None
    reasons: list[str] | None
    strengthened_factors: list[str]
    weakened_factors: list[str]
    data_status: TimelineDataStatus


@dataclass(frozen=True)
class TimelineSummary:
    entries: list[TimelineEntry]  # newest first for display


def _factor_label(name: str) -> str:
    return FACTOR_LABELS.get(name, name.replace("_", " ").title())


def _factor_deltas(
    prev_factors: dict[str, float] | None, curr_factors: dict[str, float] | None
) -> tuple[list[str], list[str]]:
    if not prev_factors or not curr_factors:
        return [], []

    strengthened: list[str] = []
    weakened: list[str] = []
    for name, curr_score in curr_factors.items():
        prev_score = prev_factors.get(name)
        if prev_score is None:
            continue
        delta = curr_score - prev_score
        if delta >= FACTOR_CHANGE_THRESHOLD:
            strengthened.append(_factor_label(name))
        elif delta <= -FACTOR_CHANGE_THRESHOLD:
            weakened.append(_factor_label(name))
    return strengthened, weakened


def _change_summary(prev: AIAnalysis | None, row: AIAnalysis) -> str | None:
    if prev is None:
        return "First recorded analysis for this symbol/timeframe."

    parts: list[str] = []
    if row.direction != prev.direction:
        parts.append(f"Direction {prev.direction} → {row.direction}")
    if abs(row.confidence - prev.confidence) >= CONFIDENCE_CHANGE_THRESHOLD:
        parts.append(f"Confidence {prev.confidence:.0f} → {row.confidence:.0f}")
    if abs(row.score - prev.score) >= SCORE_CHANGE_THRESHOLD:
        parts.append(f"Market Score {prev.score:.0f} → {row.score:.0f}")
    return "; ".join(parts) if parts else None


def _to_entry(prev: AIAnalysis | None, row: AIAnalysis, summary: str | None) -> TimelineEntry:
    strengthened, weakened = _factor_deltas(prev.factors if prev else None, row.factors)
    data_status: TimelineDataStatus = "OK" if row.factors is not None and row.reasons is not None else "AWAITING_DATA"
    return TimelineEntry(
        time=row.time,
        score=row.score,
        confidence=row.confidence,
        direction=row.direction,
        change_summary=summary,
        reasons=row.reasons,
        strengthened_factors=strengthened,
        weakened_factors=weakened,
        data_status=data_status,
    )


async def get_timeline(db: AsyncSession, symbol: str, interval: str, limit: int = TIMELINE_LIMIT) -> TimelineSummary:
    rows = await get_recent_analysis(db, symbol, interval, limit=limit)  # ascending: oldest -> newest

    entries: list[TimelineEntry] = []
    prev: AIAnalysis | None = None
    for row in rows:
        summary = _change_summary(prev, row)
        is_change_point = prev is None or summary is not None
        if is_change_point:
            entries.append(_to_entry(prev, row, summary))
        prev = row

    return TimelineSummary(entries=list(reversed(entries)))
