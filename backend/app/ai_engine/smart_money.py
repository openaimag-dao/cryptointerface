"""Smart Money / ICT concepts block (Sprint 8 spec, completed in Sprint 6).

Sprint 8 shipped three concepts derived honestly from the same swing-point
detector `app/ai_engine/scoring/structure.py` already uses
(`find_swing_indices` in `app/ai_engine/types.py`): Equal Highs, Equal Lows,
Break of Structure. The other five — Order Blocks, Fair Value Gaps,
Liquidity Zones, Change of Character, Liquidity Sweep — shipped as
`NOT_YET_IMPLEMENTED` stubs because no detector existed yet.

Sprint 6 implements all five, each from a standard, deterministic
ICT/SMC definition computed directly off real OHLCV — no ML, no
fabricated levels:

- **Change of Character**: reuses `_break_of_structure` plus a trend-state
  read from the last two swing highs/lows. A structural break only counts
  as CHoCH when it runs *against* the established trend (the first sign of
  a reversal); a break that continues the trend is still just a BOS.
- **Order Blocks**: the last opposite-colored candle immediately before the
  most recent impulse candle (body > 1.5x the recent average body).
- **Fair Value Gaps**: the classic 3-candle imbalance (candle 3's low above
  candle 1's high, or vice versa), reported only while unfilled by a later
  candle.
- **Liquidity Zones**: a volume-profile read — the highest-volume price
  band (by typical price) over the recent window, relative to current price.
- **Liquidity Sweep**: a wick beyond the most recent swing high/low that
  closes back inside it — the standard stop-hunt-then-reverse signature.

Each concept is a small, independent function in `_CONCEPT_BUILDERS` below —
the same one-function-per-concept shape Sprint 8 established, so any future
concept is one more function with this signature.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np

from app.ai_engine.types import find_swing_indices

SmartMoneyStatus = Literal["BULLISH", "BEARISH", "NEUTRAL", "NOT_YET_IMPLEMENTED"]

SWING_WINDOW = 3
EQUAL_LEVEL_TOLERANCE_PCT = 0.15  # two swings within this % of each other count as "equal"
IMPULSE_BODY_MULTIPLE = 1.5  # a candle body this many times the recent average counts as an "impulse"
IMPULSE_LOOKBACK = 10  # how many recent candles to scan for an impulse candle
FVG_LOOKBACK = 20  # how many recent candles to scan for an unfilled 3-candle gap
LIQUIDITY_ZONE_LOOKBACK = 50  # volume-profile window
LIQUIDITY_ZONE_BINS = 20


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


def _trend_state(highs: np.ndarray, lows: np.ndarray) -> Literal["UPTREND", "DOWNTREND", "RANGING", "UNKNOWN"]:
    """Higher-highs+higher-lows / lower-highs+lower-lows read off the last
    two swing points on each side — the textbook Dow-theory trend test."""
    swing_high_idx = find_swing_indices(highs, SWING_WINDOW, find_highs=True)
    swing_low_idx = find_swing_indices(lows, SWING_WINDOW, find_highs=False)
    if len(swing_high_idx) < 2 or len(swing_low_idx) < 2:
        return "UNKNOWN"

    higher_high = highs[swing_high_idx[-1]] > highs[swing_high_idx[-2]]
    higher_low = lows[swing_low_idx[-1]] > lows[swing_low_idx[-2]]
    lower_high = highs[swing_high_idx[-1]] < highs[swing_high_idx[-2]]
    lower_low = lows[swing_low_idx[-1]] < lows[swing_low_idx[-2]]

    if higher_high and higher_low:
        return "UPTREND"
    if lower_high and lower_low:
        return "DOWNTREND"
    return "RANGING"


def _change_of_character(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> SmartMoneyConcept:
    """CHoCH is a Break of Structure that runs *against* the established
    trend — the first sign of a possible reversal, as distinct from a BOS
    that simply continues it."""
    trend = _trend_state(highs, lows)
    if trend == "UNKNOWN":
        return SmartMoneyConcept(
            "Change of Character", "NEUTRAL", None, "Not enough swing history to establish a trend yet."
        )

    bos = _break_of_structure(closes, highs, lows)
    if bos.status == "NEUTRAL":
        return SmartMoneyConcept(
            "Change of Character", "NEUTRAL", None, "No structural break yet to compare against the prevailing trend."
        )
    if trend == "UPTREND" and bos.status == "BEARISH":
        return SmartMoneyConcept(
            "Change of Character",
            "BEARISH",
            bos.value,
            "Price broke down through prior structure while the market was in an uptrend — first sign of a possible reversal.",
        )
    if trend == "DOWNTREND" and bos.status == "BULLISH":
        return SmartMoneyConcept(
            "Change of Character",
            "BULLISH",
            bos.value,
            "Price broke up through prior structure while the market was in a downtrend — first sign of a possible reversal.",
        )
    return SmartMoneyConcept(
        "Change of Character",
        "NEUTRAL",
        None,
        "The latest structural break continues the prevailing trend — that's a Break of Structure, not a character change.",
    )


def _order_blocks(opens: np.ndarray, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> SmartMoneyConcept:
    """The last opposite-colored candle immediately before the most recent
    impulse move — the standard ICT order-block definition."""
    n = len(closes)
    if n < 6:
        return SmartMoneyConcept("Order Blocks", "NEUTRAL", None, "Not enough candle history yet.")

    bodies = np.abs(closes - opens)
    avg_body = float(np.mean(bodies[:-1]))
    if avg_body <= 0:
        return SmartMoneyConcept("Order Blocks", "NEUTRAL", None, "No meaningful candle bodies to compare against.")

    lookback = min(IMPULSE_LOOKBACK, n - 1)
    impulse_idx: int | None = None
    for i in range(n - 1, max(0, n - 1 - lookback), -1):
        if bodies[i] > IMPULSE_BODY_MULTIPLE * avg_body:
            impulse_idx = i
            break

    if impulse_idx is None or impulse_idx == 0:
        return SmartMoneyConcept(
            "Order Blocks", "NEUTRAL", None, "No strong impulse candle found in recent history to anchor an order block."
        )

    impulse_bullish = closes[impulse_idx] > opens[impulse_idx]
    for j in range(impulse_idx - 1, -1, -1):
        candle_bullish = closes[j] > opens[j]
        if impulse_bullish and not candle_bullish:
            return SmartMoneyConcept(
                "Order Blocks",
                "BULLISH",
                f"{float(lows[j]):.6g}-{float(highs[j]):.6g}",
                "Last bearish candle before a strong bullish impulse — a bullish order-block zone.",
            )
        if not impulse_bullish and candle_bullish:
            return SmartMoneyConcept(
                "Order Blocks",
                "BEARISH",
                f"{float(lows[j]):.6g}-{float(highs[j]):.6g}",
                "Last bullish candle before a strong bearish impulse — a bearish order-block zone.",
            )

    return SmartMoneyConcept(
        "Order Blocks", "NEUTRAL", None, "No opposite-colored candle found immediately before the impulse move."
    )


def _fair_value_gaps(highs: np.ndarray, lows: np.ndarray) -> SmartMoneyConcept:
    """Classic 3-candle imbalance: candle 3's low above candle 1's high
    (bullish gap) or candle 3's high below candle 1's low (bearish gap),
    reported only while a later candle hasn't traded back through it."""
    n = len(highs)
    if n < 3:
        return SmartMoneyConcept("Fair Value Gaps", "NEUTRAL", None, "Not enough candle history yet.")

    lookback = min(FVG_LOOKBACK, n - 2)
    for i in range(n - 1, n - 1 - lookback, -1):
        if i < 2:
            break
        low3, high1 = float(lows[i]), float(highs[i - 2])
        high3, low1 = float(highs[i]), float(lows[i - 2])

        if low3 > high1 and not _range_traded(lows, highs, i + 1, n, high1, low3):
            return SmartMoneyConcept(
                "Fair Value Gaps",
                "BULLISH",
                f"{high1:.6g}-{low3:.6g}",
                "Unfilled bullish imbalance between three candles — price may return to fill it.",
            )
        if high3 < low1 and not _range_traded(lows, highs, i + 1, n, high3, low1):
            return SmartMoneyConcept(
                "Fair Value Gaps",
                "BEARISH",
                f"{high3:.6g}-{low1:.6g}",
                "Unfilled bearish imbalance between three candles — price may return to fill it.",
            )

    return SmartMoneyConcept("Fair Value Gaps", "NEUTRAL", None, "No unfilled 3-candle imbalance found in recent history.")


def _range_traded(lows: np.ndarray, highs: np.ndarray, start: int, end: int, low: float, high: float) -> bool:
    for k in range(start, end):
        if float(lows[k]) <= high and float(highs[k]) >= low:
            return True
    return False


def _liquidity_zones(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> SmartMoneyConcept:
    """Volume-profile read: the highest-volume price band (by typical
    price) over the recent window, relative to current price."""
    n = len(closes)
    if n < 10:
        return SmartMoneyConcept("Liquidity Zones", "NEUTRAL", None, "Not enough candle history yet.")

    lookback = min(LIQUIDITY_ZONE_LOOKBACK, n)
    seg_highs, seg_lows, seg_vol = highs[-lookback:], lows[-lookback:], volumes[-lookback:]
    price_min, price_max = float(seg_lows.min()), float(seg_highs.max())
    if price_max <= price_min or float(seg_vol.sum()) <= 0:
        return SmartMoneyConcept("Liquidity Zones", "NEUTRAL", None, "No meaningful price range or volume to profile.")

    typical_price = (seg_highs + seg_lows) / 2.0
    hist, edges = np.histogram(typical_price, bins=LIQUIDITY_ZONE_BINS, range=(price_min, price_max), weights=seg_vol)
    top_bin = int(np.argmax(hist))
    zone_low, zone_high = float(edges[top_bin]), float(edges[top_bin + 1])
    zone_mid = (zone_low + zone_high) / 2.0
    current_price = float(closes[-1])

    if zone_mid > current_price * 1.001:
        return SmartMoneyConcept(
            "Liquidity Zones",
            "BEARISH",
            f"{zone_low:.6g}-{zone_high:.6g}",
            f"Highest-volume price band in the last {lookback} candles sits above current price — a resting pool of interest overhead.",
        )
    if zone_mid < current_price * 0.999:
        return SmartMoneyConcept(
            "Liquidity Zones",
            "BULLISH",
            f"{zone_low:.6g}-{zone_high:.6g}",
            f"Highest-volume price band in the last {lookback} candles sits below current price — a resting pool of interest underneath.",
        )
    return SmartMoneyConcept(
        "Liquidity Zones",
        "NEUTRAL",
        f"{zone_low:.6g}-{zone_high:.6g}",
        f"Highest-volume price band in the last {lookback} candles sits right around current price.",
    )


def _liquidity_sweep(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> SmartMoneyConcept:
    """A wick beyond the most recent swing high/low that closes back
    inside it — the standard stop-hunt-then-reverse signature."""
    if len(closes) < 2:
        return SmartMoneyConcept("Liquidity Sweep", "NEUTRAL", None, "Not enough candle history yet.")

    swing_high_idx = find_swing_indices(highs[:-1], SWING_WINDOW, find_highs=True)
    swing_low_idx = find_swing_indices(lows[:-1], SWING_WINDOW, find_highs=False)
    last_high, last_low, last_close = float(highs[-1]), float(lows[-1]), float(closes[-1])

    if swing_high_idx:
        prior_high = float(highs[swing_high_idx[-1]])
        if last_high > prior_high and last_close < prior_high:
            return SmartMoneyConcept(
                "Liquidity Sweep",
                "BEARISH",
                f"{prior_high:.6g}",
                f"Price wicked above the prior swing-high at {prior_high:.6g} then closed back below it — likely a stop-hunt of buy-side liquidity before reversing down.",
            )
    if swing_low_idx:
        prior_low = float(lows[swing_low_idx[-1]])
        if last_low < prior_low and last_close > prior_low:
            return SmartMoneyConcept(
                "Liquidity Sweep",
                "BULLISH",
                f"{prior_low:.6g}",
                f"Price wicked below the prior swing-low at {prior_low:.6g} then closed back above it — likely a stop-hunt of sell-side liquidity before reversing up.",
            )

    return SmartMoneyConcept(
        "Liquidity Sweep", "NEUTRAL", None, "No wick-through-and-reject pattern at the most recent swing level."
    )


# Every concept takes (opens, highs, lows, closes, volumes) so each one —
# regardless of which fields it actually needs — has the same call
# signature, keeping it a one-line addition to extend this list further.
_CONCEPT_BUILDERS: list[Callable[[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray], SmartMoneyConcept]] = [
    lambda opens, highs, lows, closes, volumes: _break_of_structure(closes, highs, lows),
    lambda opens, highs, lows, closes, volumes: _equal_highs(highs),
    lambda opens, highs, lows, closes, volumes: _equal_lows(lows),
    lambda opens, highs, lows, closes, volumes: _change_of_character(closes, highs, lows),
    lambda opens, highs, lows, closes, volumes: _order_blocks(opens, closes, highs, lows),
    lambda opens, highs, lows, closes, volumes: _fair_value_gaps(highs, lows),
    lambda opens, highs, lows, closes, volumes: _liquidity_zones(closes, highs, lows, volumes),
    lambda opens, highs, lows, closes, volumes: _liquidity_sweep(closes, highs, lows),
]


def analyze_smart_money(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    opens: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> list[SmartMoneyConcept]:
    """`opens`/`volumes` default to arrays of zeros when omitted so the three
    Sprint-8 concepts (which never needed them) keep working unchanged for
    any existing caller — but every real read here needs the full candle,
    so callers should pass the actual opens/volumes."""
    n = len(closes)
    if opens is None:
        opens = np.zeros(n)
    if volumes is None:
        volumes = np.zeros(n)
    return [builder(opens, highs, lows, closes, volumes) for builder in _CONCEPT_BUILDERS]
