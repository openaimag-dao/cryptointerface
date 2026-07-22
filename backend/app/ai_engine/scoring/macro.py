"""Macro Engine (Sprint 4).

Reads the latest macro snapshot (`app/services/macro_repository.py`,
populated by `app/intelligence/macro/`) and scores it against crypto risk
sentiment. `market_score.py` was already shaped for this since Sprint 3
(see its docstring) — this file only had to replace the stub body and the
weight moved from 0.00 to a real value.

Every ETF-proxied indicator (DXY/Gold/S&P 500/NASDAQ/VIX — see
`app/intelligence/macro/symbols.py`) is scored off its **% change since
the previous reading**, not its absolute level: a proxy ETF's share price
doesn't sit on the same scale as the underlying index (VIXY trades in the
teens, the VIX index itself has its own 10-80 fear/complacency bands), so
level-based thresholds would be meaningless. US 10Y is a real yield
(scored the same way, by % change, for consistency). Fear & Greed is the
one exception — it's already a 0-100 sentiment index designed to be read
directly, so it's scored by level, not change.

Silver, Oil, and BTC Dominance are fetched and displayed
(`/api/macro/indicators`) but not scored here — see
`MacroIndicatorDef.used_in_scoring` for why each is excluded.

Score composition (starts at neutral 50, each capped independently):
  +/-10  NASDAQ change (strongest crypto-correlated equity index)
  +/-8   DXY change (inverted: weaker dollar -> bullish)
  +/-8   S&P 500 change
  +/-8   VIX proxy change (inverted: rising fear -> bearish)
  +/-12  Fear & Greed level (distance from neutral 50, direct not contrarian)
  +/-6   US 10Y yield change (inverted: rising yield -> bearish)
  +/-5   Gold change (inverted: rising safe-haven demand -> mildly bearish)
Missing indicators simply contribute no points (no reading fetched yet is
not the same as a neutral reading — it's an unopinionated one).
"""

from app.ai_engine.types import FactorScore, MacroIndicatorReading, MacroSnapshot, clamp, make_factor_score

# (label, max_points, inverted) — inverted means "reading up" -> bearish
_CHANGE_SCORED_FIELDS: list[tuple[str, str, float, bool]] = [
    ("nasdaq", "NASDAQ", 10.0, False),
    ("dxy", "DXY", 8.0, True),
    ("sp500", "S&P 500", 8.0, False),
    ("vix", "VIX proxy", 8.0, True),
    ("us10y", "US 10Y yield", 6.0, True),
    ("gold", "Gold", 5.0, True),
]
CHANGE_SCALE = 3.0  # 1% move -> 3 points, before the per-field cap
FEAR_GREED_MAX_POINTS = 12.0


def _score_change_field(reading: MacroIndicatorReading | None, label: str, max_points: float, inverted: bool):
    """Returns (bullish_points, bearish_points, reason|None)."""
    if reading is None or reading.change_percent is None:
        return 0.0, 0.0, None

    change = reading.change_percent
    points = clamp(abs(change) * CHANGE_SCALE, 0, max_points)
    if points == 0:
        return 0.0, 0.0, None

    moved_up = change > 0
    is_bullish = moved_up != inverted  # inverted fields flip the read
    direction_word = "up" if moved_up else "down"
    if is_bullish:
        return points, 0.0, f"{label} {direction_word} {abs(change):.2f}% — bullish tailwind for risk assets"
    return 0.0, points, f"{label} {direction_word} {abs(change):.2f}% — bearish headwind for risk assets"


def score_macro(snapshot: MacroSnapshot | None) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    if snapshot is None:
        reasons.append(
            "Macro data not yet available (Alpha Vantage key not configured, or the scheduler hasn't "
            "polled yet) — neutral, zero-conviction read"
        )
        details["stub"] = True
        factor = make_factor_score("macro", 50.0, reasons, details)
        factor.details["macro_score"] = factor.score
        factor.details["macro_direction"] = factor.direction
        factor.details["macro_strength"] = factor.strength
        return factor

    for field_name, label, max_points, inverted in _CHANGE_SCORED_FIELDS:
        reading: MacroIndicatorReading | None = getattr(snapshot, field_name)
        points_bull, points_bear, reason = _score_change_field(reading, label, max_points, inverted)
        bullish += points_bull
        bearish += points_bear
        if reason:
            reasons.append(reason)
        if reading is not None:
            details[f"{field_name}_value"] = reading.value
            if reading.change_percent is not None:
                details[f"{field_name}_change_percent"] = round(reading.change_percent, 3)

    if snapshot.fear_greed is not None:
        fg_value = snapshot.fear_greed.value
        details["fear_greed_value"] = fg_value
        distance = fg_value - 50.0
        points = clamp(abs(distance) / 50.0 * FEAR_GREED_MAX_POINTS, 0, FEAR_GREED_MAX_POINTS)
        if points > 0:
            if distance > 0:
                bullish += points
                reasons.append(f"Crypto Fear & Greed Index at {fg_value:.0f} (greed) — bullish sentiment tilt")
            else:
                bearish += points
                reasons.append(f"Crypto Fear & Greed Index at {fg_value:.0f} (fear) — bearish sentiment tilt")

    if not reasons:
        reasons.append("Macro readings available but none moved enough to register a directional tilt")

    score = 50.0 + bullish - bearish
    factor = make_factor_score("macro", score, reasons, details)
    factor.details["macro_score"] = factor.score
    factor.details["macro_direction"] = factor.direction
    factor.details["macro_strength"] = factor.strength
    return factor
