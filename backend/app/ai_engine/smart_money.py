"""Smart Money / ICT concepts block (Sprint 8 spec).

The spec explicitly scopes this stage to "use the existing AI Engine for
now" and "keep the architecture easy to extend" — so this module does
**not** invent seven new, unvalidated pattern-detection algorithms.
Instead:

- **Equal Highs / Equal Lows / Break of Structure** are derived honestly
  from the same swing-point detector `app/ai_engine/scoring/structure.py`
  already uses (`find_swing_indices` in `app/ai_engine/types.py`) — real
  reads, not placeholders, because the underlying data already exists.
- **Order Blocks, Fair Value Gaps, Liquidity Zones, Change of Character,
  and Liquidity Sweeps** are genuine ICT/SMC concepts with no detector
  anywhere in this codebase yet. Each is reported as `NOT_YET_IMPLEMENTED`
  rather than a fabricated read.

Each concept is a small, independent function in `_CONCEPT_BUILDERS`
below — adding a real detector for e.g. Order Blocks later means writing
one new function with this same signature and swapping it in, without
touching anything else in this module or its caller.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np

from app.ai_engine.types import find_swing_indices

SmartMoneyStatus = Literal["BULLISH", "BEARISH", "NEUTRAL", "NOT_YET_IMPLEMENTED"]

SWING_WINDOW = 3
EQUAL_LEVEL_TOLERANCE_PCT = 0.15  # two swings within this % of each other count as "equal"


@dataclass(frozen=True)
class SmartMoneyConcept:
    name: str
    status: SmartMoneyStatus
    value: str | None
    explanation: str


def _equal_highs(highs: np.ndarray) -> SmartMoneyConcept:
    swing_idx = find_swing_indices(highs, SWING_WINDOW, find_highs=True)
    if len(swing_idx) < 2:
        return SmartMoneyConcept("Equal Highs", "NEUTRAL", None, "Not enough swing highs identified yet.")

    a, b = float(highs[swing_idx[-2]]), float(highs[swing_idx[-1]])
    tolerance = max(a, b) * (EQUAL_LEVEL_TOLERANCE_PCT / 100.0)
    if abs(a - b) <= tolerance:
        return SmartMoneyConcept(
            "Equal Highs",
            "BEARISH",
            f"{a:.6g} / {b:.6g}",
            "The last two swing highs sit within a tight band — often a liquidity pool resting above price.",
        )
    return SmartMoneyConcept("Equal Highs", "NEUTRAL", f"{a:.6g} / {b:.6g}", "The last two swing highs are not equal.")


def _equal_lows(lows: np.ndarray) -> SmartMoneyConcept:
    swing_idx = find_swing_indices(lows, SWING_WINDOW, find_highs=False)
    if len(swing_idx) < 2:
        return SmartMoneyConcept("Equal Lows", "NEUTRAL", None, "Not enough swing lows identified yet.")

    a, b = float(lows[swing_idx[-2]]), float(lows[swing_idx[-1]])
    tolerance = max(a, b) * (EQUAL_LEVEL_TOLERANCE_PCT / 100.0)
    if abs(a - b) <= tolerance:
        return SmartMoneyConcept(
            "Equal Lows",
            "BULLISH",
            f"{a:.6g} / {b:.6g}",
            "The last two swing lows sit within a tight band — often a liquidity pool resting below price.",
        )
    return SmartMoneyConcept("Equal Lows", "NEUTRAL", f"{a:.6g} / {b:.6g}", "The last two swing lows are not equal.")


def _break_of_structure(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> SmartMoneyConcept:
    """Same breakout condition `scoring/structure.py` already uses:
    price trading beyond the most recent swing high/low."""
    price = float(closes[-1])
    swing_high_idx = find_swing_indices(highs, SWING_WINDOW, find_highs=True)
    swing_low_idx = find_swing_indices(lows, SWING_WINDOW, find_highs=False)

    if swing_high_idx and price > float(highs[swing_high_idx[-1]]):
        level = float(highs[swing_high_idx[-1]])
        return SmartMoneyConcept(
            "Break of Structure",
            "BULLISH",
            f"{level:.6g}",
            f"Price broke above the prior swing-high at {level:.6g} — bullish structure shift.",
        )
    if swing_low_idx and price < float(lows[swing_low_idx[-1]]):
        level = float(lows[swing_low_idx[-1]])
        return SmartMoneyConcept(
            "Break of Structure",
            "BEARISH",
            f"{level:.6g}",
            f"Price broke below the prior swing-low at {level:.6g} — bearish structure shift.",
        )
    return SmartMoneyConcept(
        "Break of Structure", "NEUTRAL", None, "Price is still inside the prior swing range — no break yet."
    )


def _not_yet_implemented(
    name: str, description: str
) -> Callable[[np.ndarray, np.ndarray, np.ndarray], SmartMoneyConcept]:
    def _builder(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> SmartMoneyConcept:
        return SmartMoneyConcept(name, "NOT_YET_IMPLEMENTED", None, description)

    return _builder


# Each entry takes (closes, highs, lows) so every concept — implemented or
# not — has the same call signature, making it a one-line swap to add a
# real detector later.
_CONCEPT_BUILDERS: list[Callable[[np.ndarray, np.ndarray, np.ndarray], SmartMoneyConcept]] = [
    lambda closes, highs, lows: _break_of_structure(closes, highs, lows),
    lambda closes, highs, lows: _equal_highs(highs),
    lambda closes, highs, lows: _equal_lows(lows),
    _not_yet_implemented(
        "Change of Character",
        "Needs real trend-state tracking (first opposite-direction break after a confirmed trend) — not yet built.",
    ),
    _not_yet_implemented(
        "Order Blocks", "Needs a dedicated last-opposing-candle-before-a-strong-move detector — not yet built."
    ),
    _not_yet_implemented(
        "Fair Value Gaps",
        "Needs a three-candle imbalance detector (gap between candle 1's wick and candle 3's wick) — not yet built.",
    ),
    _not_yet_implemented("Liquidity Zones", "Needs volume-profile-style price-level clustering — not yet built."),
    _not_yet_implemented(
        "Liquidity Sweep", "Needs wick-through-then-reject-a-liquidity-pool detection — not yet built."
    ),
]


def analyze_smart_money(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> list[SmartMoneyConcept]:
    return [builder(closes, highs, lows) for builder in _CONCEPT_BUILDERS]
