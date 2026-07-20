"""Volume Engine.

Reads raw volume trend, On-Balance Volume, VWAP deviation, and an
approximated delta volume into a single volume score.

Binance klines don't expose tick-level buy/sell delta volume, so "delta
volume" here is approximated from candle-close direction (an up candle's
volume counts as buying pressure, a down candle's as selling pressure) —
this is called out explicitly in the reasons so it's never confused with a
true order-flow delta.

Score composition (starts at neutral 50):
  +/-15  Volume rising/falling, aligned with the price move over the same window
  +/-20  OBV trending in a given direction, scaled by its slope
  +/-15  Price deviation from VWAP
  +/-15  Approximated delta volume skew (up-volume vs down-volume)
"""

import numpy as np

from app.ai_engine.types import FactorScore, clamp, last_valid, make_factor_score
from app.services.indicators.obv import obv
from app.services.indicators.vwap import vwap

VOLUME_LOOKBACK_BARS = 20
VOLUME_SURGE_THRESHOLD_PCT = 15.0
OBV_LOOKBACK_BARS = 20
VWAP_DEVIATION_SCALE = 5.0
DELTA_VOLUME_LOOKBACK_BARS = 20


def score_volume(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    if len(volumes) >= VOLUME_LOOKBACK_BARS * 2:
        recent_avg = float(np.mean(volumes[-VOLUME_LOOKBACK_BARS:]))
        prior_avg = float(np.mean(volumes[-2 * VOLUME_LOOKBACK_BARS : -VOLUME_LOOKBACK_BARS]))
        details["recent_avg_volume"] = round(recent_avg, 2)
        details["prior_avg_volume"] = round(prior_avg, 2)
        if prior_avg > 0:
            volume_change_pct = (recent_avg - prior_avg) / prior_avg * 100
            details["volume_change_pct"] = round(volume_change_pct, 2)
            price_change = closes[-1] - closes[-1 - VOLUME_LOOKBACK_BARS]
            if volume_change_pct > VOLUME_SURGE_THRESHOLD_PCT:
                points = clamp(volume_change_pct * 0.2, 0, 15)
                if price_change > 0:
                    bullish += points
                    reasons.append(f"Volume rising ({volume_change_pct:.1f}%) confirming the upward price move")
                elif price_change < 0:
                    bearish += points
                    reasons.append(f"Volume rising ({volume_change_pct:.1f}%) confirming the downward price move")
            elif volume_change_pct < -VOLUME_SURGE_THRESHOLD_PCT:
                reasons.append(f"Volume declining ({volume_change_pct:.1f}%), weaker participation")
    else:
        reasons.append("Not enough history yet for a volume trend read")

    obv_series = obv(closes, volumes)
    if len(obv_series) > OBV_LOOKBACK_BARS:
        obv_last = float(obv_series[-1])
        obv_prev = float(obv_series[-1 - OBV_LOOKBACK_BARS])
        obv_delta = obv_last - obv_prev
        details["obv"] = round(obv_last, 2)
        typical_volume = float(np.mean(volumes[-OBV_LOOKBACK_BARS:]))
        if typical_volume > 0:
            obv_slope_ratio = obv_delta / (typical_volume * OBV_LOOKBACK_BARS)
            details["obv_slope_ratio"] = round(obv_slope_ratio, 4)
            points = clamp(abs(obv_slope_ratio) * 40, 0, 20)
            if obv_delta > 0 and points >= 3:
                bullish += points
                reasons.append("OBV trending higher (buying pressure accumulating)")
            elif obv_delta < 0 and points >= 3:
                bearish += points
                reasons.append("OBV trending lower (selling pressure accumulating)")
    else:
        reasons.append("Not enough history yet for an OBV trend read")

    vwap_last = last_valid(vwap(highs, lows, closes, volumes))
    if vwap_last is not None and vwap_last > 0:
        details["vwap"] = round(vwap_last, 4)
        vwap_deviation_pct = (closes[-1] - vwap_last) / vwap_last * 100
        details["vwap_deviation_pct"] = round(vwap_deviation_pct, 3)
        points = clamp(abs(vwap_deviation_pct) * VWAP_DEVIATION_SCALE, 0, 15)
        if vwap_deviation_pct > 0:
            bullish += points
            if points >= 3:
                reasons.append(f"Price trading {vwap_deviation_pct:.2f}% above VWAP (buyers in control)")
        elif vwap_deviation_pct < 0:
            bearish += points
            if points >= 3:
                reasons.append(f"Price trading {abs(vwap_deviation_pct):.2f}% below VWAP (sellers in control)")
    else:
        reasons.append("Not enough history yet for a VWAP read")

    if len(closes) > DELTA_VOLUME_LOOKBACK_BARS:
        window_closes = closes[-DELTA_VOLUME_LOOKBACK_BARS - 1 :]
        window_volumes = volumes[-DELTA_VOLUME_LOOKBACK_BARS:]
        up_volume = 0.0
        down_volume = 0.0
        for i in range(1, len(window_closes)):
            if window_closes[i] > window_closes[i - 1]:
                up_volume += float(window_volumes[i - 1])
            elif window_closes[i] < window_closes[i - 1]:
                down_volume += float(window_volumes[i - 1])
        total_volume = up_volume + down_volume
        if total_volume > 0:
            delta_ratio = (up_volume - down_volume) / total_volume
            details["approx_delta_volume_ratio"] = round(delta_ratio, 4)
            points = clamp(abs(delta_ratio) * 15, 0, 15)
            if delta_ratio > 0 and points >= 3:
                bullish += points
                reasons.append(
                    "Approximated delta volume skewed toward buyers "
                    "(true tick-level delta volume isn't available from klines)"
                )
            elif delta_ratio < 0 and points >= 3:
                bearish += points
                reasons.append(
                    "Approximated delta volume skewed toward sellers "
                    "(true tick-level delta volume isn't available from klines)"
                )
    else:
        reasons.append("Not enough history yet for a delta-volume approximation")

    score = 50.0 + bullish - bearish
    if not reasons:
        reasons.append("Insufficient candle history for a volume read")

    factor = make_factor_score("volume", score, reasons, details)
    factor.details["volume_score"] = factor.score
    factor.details["volume_direction"] = factor.direction
    factor.details["volume_strength"] = factor.strength
    return factor
