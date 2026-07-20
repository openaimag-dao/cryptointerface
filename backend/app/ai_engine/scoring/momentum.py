"""Momentum Engine.

Reads RSI, MACD (line/signal/histogram), and Stochastic RSI into a single
momentum score.

Score composition (starts at neutral 50):
  +/-25  RSI distance from the neutral 50 line, scaled and capped
  +/-15  MACD line vs signal line (bullish/bearish crossover)
  +/-10  MACD histogram expanding in the direction it already points
         (accelerating momentum)
  +/-15  Stochastic RSI %K vs %D crossover
Max/min score is clamped to [0, 100] by `make_factor_score`.
"""

import numpy as np

from app.ai_engine.types import FactorScore, clamp, last_valid, make_factor_score
from app.services.indicators.macd import macd
from app.services.indicators.rsi import rsi
from app.services.indicators.stoch_rsi import stoch_rsi

RSI_PERIOD = 14
RSI_SCALE = 0.6  # RSI at 0 or 100 (50 away from neutral) -> 30 points, capped at 25
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
HISTOGRAM_LOOKBACK_BARS = 3
STOCH_OVERBOUGHT = 80.0
STOCH_OVERSOLD = 20.0


def score_momentum(closes: np.ndarray) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    rsi_last = last_valid(rsi(closes, RSI_PERIOD))
    if rsi_last is not None:
        details["rsi"] = round(rsi_last, 2)
        delta = rsi_last - 50.0
        points = clamp(abs(delta) * RSI_SCALE, 0, 25)
        if delta > 0:
            bullish += points
            reasons.append(f"RSI at {rsi_last:.1f}, above the neutral 50 line (bullish momentum)")
        elif delta < 0:
            bearish += points
            reasons.append(f"RSI at {rsi_last:.1f}, below the neutral 50 line (bearish momentum)")
        if rsi_last >= RSI_OVERBOUGHT:
            reasons.append(f"RSI in overbought territory ({rsi_last:.1f} >= {RSI_OVERBOUGHT:.0f})")
        elif rsi_last <= RSI_OVERSOLD:
            reasons.append(f"RSI in oversold territory ({rsi_last:.1f} <= {RSI_OVERSOLD:.0f})")
    else:
        reasons.append("Not enough history yet for an RSI read")

    macd_line, signal_line, histogram = macd(closes)
    macd_last = last_valid(macd_line)
    signal_last = last_valid(signal_line)
    if macd_last is not None and signal_last is not None:
        details["macd"] = round(macd_last, 4)
        details["macd_signal"] = round(signal_last, 4)
        if macd_last > signal_last:
            bullish += 15.0
            reasons.append("MACD line above signal line (bullish crossover)")
        else:
            bearish += 15.0
            reasons.append("MACD line below signal line (bearish crossover)")
    else:
        reasons.append("Not enough history yet for a MACD read")

    hist_valid = histogram[~np.isnan(histogram)]
    if len(hist_valid) >= HISTOGRAM_LOOKBACK_BARS:
        recent = hist_valid[-HISTOGRAM_LOOKBACK_BARS:]
        details["macd_histogram"] = round(float(recent[-1]), 4)
        if recent[-1] > recent[0] and recent[-1] > 0:
            bullish += 10.0
            reasons.append("MACD histogram expanding positively (accelerating bullish momentum)")
        elif recent[-1] < recent[0] and recent[-1] < 0:
            bearish += 10.0
            reasons.append("MACD histogram expanding negatively (accelerating bearish momentum)")

    stoch_k, stoch_d = stoch_rsi(closes)
    k_last = last_valid(stoch_k)
    d_last = last_valid(stoch_d)
    if k_last is not None and d_last is not None:
        details["stoch_rsi_k"] = round(k_last, 2)
        details["stoch_rsi_d"] = round(d_last, 2)
        if k_last > d_last:
            bullish += 15.0
            reasons.append("Stochastic RSI %K above %D (bullish crossover)")
        else:
            bearish += 15.0
            reasons.append("Stochastic RSI %K below %D (bearish crossover)")
        if k_last >= STOCH_OVERBOUGHT:
            reasons.append(f"Stochastic RSI overbought ({k_last:.1f} >= {STOCH_OVERBOUGHT:.0f})")
        elif k_last <= STOCH_OVERSOLD:
            reasons.append(f"Stochastic RSI oversold ({k_last:.1f} <= {STOCH_OVERSOLD:.0f})")
    else:
        reasons.append("Not enough history yet for a Stochastic RSI read")

    score = 50.0 + bullish - bearish
    if not reasons:
        reasons.append("Insufficient candle history for a momentum read")

    factor = make_factor_score("momentum", score, reasons, details)
    factor.details["momentum_score"] = factor.score
    factor.details["momentum_direction"] = factor.direction
    factor.details["momentum_strength"] = factor.strength
    return factor
