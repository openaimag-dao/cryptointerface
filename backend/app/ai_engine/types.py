"""Shared types and pure helper math used across every scoring module.

Every scoring module in `ai_engine/scoring/` returns a `FactorScore`. This
keeps `market_score.py` able to aggregate all nine factors uniformly while
each module is still free to expose extra module-specific numbers via
`details` (e.g. trend.py's `trend_strength`, `ema20`, `ema50`, ...).

Everything here is pure, synchronous, and side-effect free — no I/O, no
randomness — so it's trivially unit-testable and reproducible.
"""

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

Direction = Literal["LONG", "SHORT", "WAIT"]

# Shared score->direction thresholds, consistent with the rest of the app
# (frontend's AI-score overlay and Sprint 1's mock direction logic both use
# the same 65/35 split).
LONG_THRESHOLD = 65.0
SHORT_THRESHOLD = 35.0
NEUTRAL_SCORE = 50.0


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def direction_from_score(
    score: float, long_threshold: float = LONG_THRESHOLD, short_threshold: float = SHORT_THRESHOLD
) -> Direction:
    if score >= long_threshold:
        return "LONG"
    if score <= short_threshold:
        return "SHORT"
    return "WAIT"


def last_valid(series: np.ndarray) -> float | None:
    """The most recent non-NaN value in an indicator series, or None if the
    series is entirely NaN (not enough history yet)."""
    valid = series[~np.isnan(series)]
    return float(valid[-1]) if len(valid) else None


def last_valid_index(series: np.ndarray) -> int | None:
    """Index of the most recent non-NaN value, or None if all NaN."""
    valid_idx = np.where(~np.isnan(series))[0]
    return int(valid_idx[-1]) if len(valid_idx) else None


def find_swing_indices(values: np.ndarray, window: int, find_highs: bool) -> list[int]:
    """Indices where `values[i]` is strictly the max (or min) of its
    `2*window + 1`-bar neighborhood — a simple, deterministic swing-point
    detector (no external TA library required)."""
    indices: list[int] = []
    n = len(values)
    for i in range(window, n - window):
        segment = values[i - window : i + window + 1]
        center = window
        if find_highs and values[i] == segment.max() and np.argmax(segment) == center:
            indices.append(i)
        elif not find_highs and values[i] == segment.min() and np.argmin(segment) == center:
            indices.append(i)
    return indices


def strength_from_score(score: float) -> float:
    """How far the score sits from neutral (50), on a 0-100 scale,
    direction-agnostic. A score of exactly 50 has strength 0; a score of
    0 or 100 has strength 100."""
    return clamp(abs(score - NEUTRAL_SCORE) * 2)


@dataclass(frozen=True)
class MacroIndicatorReading:
    """One macro indicator's latest value plus its % change since the
    previous stored reading (`None` if there's no prior reading yet)."""

    value: float
    change_percent: float | None


@dataclass(frozen=True)
class MacroSnapshot:
    """Latest macro-indicator readings, built by `market_context.py` from
    `app/services/macro_repository.py` and consumed by
    `scoring/macro.py::score_macro()`. Every field is optional — a feed
    that hasn't been fetched yet (no API key configured, or the scheduler
    hasn't run) simply leaves that field `None`, and `score_macro()`
    treats a missing reading as "no opinion" rather than an error."""

    dxy: MacroIndicatorReading | None = None
    gold: MacroIndicatorReading | None = None
    sp500: MacroIndicatorReading | None = None
    nasdaq: MacroIndicatorReading | None = None
    vix: MacroIndicatorReading | None = None
    us10y: MacroIndicatorReading | None = None
    fear_greed: MacroIndicatorReading | None = None
    btc_dominance: MacroIndicatorReading | None = None


@dataclass(frozen=True)
class NewsSnapshot:
    """Recent news relevant to one symbol, built by
    `app/services/news_repository.py::get_news_snapshot_for_symbol()` and
    consumed by `scoring/news.py::score_news()`. `avg_sentiment_score` is
    already on the familiar 0-100 scale (BULLISH articles pull it toward
    100, BEARISH toward 0), weighted by each article's `impact_score` —
    a high-impact BEARISH story moves this further than a throwaway one."""

    article_count: int
    avg_sentiment_score: float
    avg_impact: float


@dataclass(frozen=True)
class FactorScore:
    """One scoring module's read on the market: a 0-100 score, the
    direction that score implies, how strongly it's expressed, and the
    human-readable reasons behind it."""

    name: str
    score: float  # 0-100
    direction: Direction
    strength: float  # 0-100, see strength_from_score
    reasons: list[str]
    details: dict[str, float | str | bool | int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "score", clamp(self.score))
        object.__setattr__(self, "strength", clamp(self.strength))


def make_factor_score(
    name: str,
    score: float,
    reasons: list[str],
    details: dict[str, float | str | bool | int] | None = None,
) -> FactorScore:
    """Convenience constructor: derives direction + strength from `score`
    so individual scoring modules only ever have to compute one number."""
    clamped = clamp(score)
    return FactorScore(
        name=name,
        score=clamped,
        direction=direction_from_score(clamped),
        strength=strength_from_score(clamped),
        reasons=reasons,
        details=details or {},
    )
