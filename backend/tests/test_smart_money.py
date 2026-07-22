import numpy as np

from app.ai_engine.smart_money import analyze_smart_money

ALL_NAMES = {
    "Break of Structure",
    "Equal Highs",
    "Equal Lows",
    "Change of Character",
    "Order Blocks",
    "Fair Value Gaps",
    "Liquidity Zones",
    "Liquidity Sweep",
}


def _by_name(concepts):
    return {c.name: c for c in concepts}


def test_analyze_smart_money_returns_eight_concepts():
    closes = np.array([100.0 + i for i in range(20)])
    highs = closes + 1
    lows = closes - 1
    concepts = analyze_smart_money(closes, highs, lows)

    assert len(concepts) == 8
    assert {c.name for c in concepts} == ALL_NAMES


def test_no_concept_is_not_yet_implemented_anymore():
    closes = np.array([100.0 + i for i in range(20)])
    highs = closes + 1
    lows = closes - 1
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    for name in ALL_NAMES:
        assert by_name[name].status != "NOT_YET_IMPLEMENTED"


def test_break_of_structure_bullish_when_price_breaks_above_prior_swing_high():
    # window=3 -> a swing high needs 3 flat/lower bars on each side. The
    # final bar (outside the detection window) then breaks decisively above it.
    highs = np.array([100, 100, 100, 106, 100, 100, 100, 100, 100, 100, 120.0])
    closes = highs
    lows = highs - 2
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Break of Structure"].status == "BULLISH"


def test_break_of_structure_bearish_when_price_breaks_below_prior_swing_low():
    lows = np.array([100, 100, 100, 94, 100, 100, 100, 100, 100, 100, 80.0])
    closes = lows
    highs = lows + 2
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Break of Structure"].status == "BEARISH"


def test_break_of_structure_neutral_inside_range():
    highs = np.array([100, 100, 100, 106, 100, 100, 100, 100, 100, 100, 103.0])
    closes = highs
    lows = highs - 2
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Break of Structure"].status == "NEUTRAL"


def test_equal_highs_detected_within_tolerance():
    # Two separated swing highs at (about) the same level -> BEARISH liquidity-pool read.
    highs = np.array([100, 100, 100, 110, 100, 100, 100, 100, 100, 100, 110.05, 100, 100, 100])
    closes = highs - 0.5
    lows = highs - 1.0
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Equal Highs"].status == "BEARISH"


def test_equal_lows_detected_within_tolerance():
    lows = np.array([100, 100, 100, 90, 100, 100, 100, 100, 100, 100, 89.98, 100, 100, 100])
    closes = lows + 0.5
    highs = lows + 1.0
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Equal Lows"].status == "BULLISH"


def test_not_enough_swings_reads_neutral():
    closes = np.array([100.0, 101.0, 102.0])
    highs = closes + 0.5
    lows = closes - 0.5
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Equal Highs"].status == "NEUTRAL"
    assert by_name["Equal Lows"].status == "NEUTRAL"


def test_change_of_character_bearish_when_uptrend_breaks_down():
    # Two rising swing highs (idx 3, 11) and two rising swing lows (idx 7, 15)
    # establish an uptrend; the final bar then breaks below the most recent
    # swing low -> CHoCH bearish (a reversal signal, not a continuation).
    n = 20
    highs = np.full(n, 100.0)
    highs[3] = 106.0
    highs[11] = 112.0
    lows = np.full(n, 100.0)
    lows[7] = 92.0
    lows[15] = 96.0
    closes = np.full(n, 100.0)
    highs[-1], lows[-1], closes[-1] = 65.0, 55.0, 60.0
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Change of Character"].status == "BEARISH"


def test_change_of_character_neutral_without_established_trend():
    closes = np.array([100.0, 101.0, 102.0])
    highs = closes + 0.5
    lows = closes - 0.5
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Change of Character"].status == "NEUTRAL"


def test_order_blocks_bullish_last_bearish_candle_before_impulse():
    opens = np.array([100.0, 101.0, 102.0, 101.5, 101.0, 100.5, 101.0])
    closes = np.array([101.0, 102.0, 101.5, 101.0, 100.5, 99.5, 115.0])  # last candle is a big impulse up
    highs = np.maximum(opens, closes) + 0.5
    lows = np.minimum(opens, closes) - 0.5
    by_name = _by_name(analyze_smart_money(closes, highs, lows, opens))

    assert by_name["Order Blocks"].status == "BULLISH"


def test_order_blocks_neutral_without_impulse():
    opens = np.array([100.0, 100.5, 101.0, 100.5, 101.0, 100.5, 101.0])
    closes = np.array([100.5, 101.0, 100.5, 101.0, 100.5, 101.0, 100.8])
    highs = np.maximum(opens, closes) + 0.2
    lows = np.minimum(opens, closes) - 0.2
    by_name = _by_name(analyze_smart_money(closes, highs, lows, opens))

    assert by_name["Order Blocks"].status == "NEUTRAL"


def test_fair_value_gap_bullish_detected_when_unfilled():
    # candle[i-2].high = 100, candle[i].low = 105 -> a bullish gap 100-105.
    highs = np.array([100.0, 100.0, 108.0])
    lows = np.array([98.0, 103.0, 105.0])
    closes = np.array([99.0, 106.0, 107.0])
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    concept = by_name["Fair Value Gaps"]
    assert concept.status == "BULLISH"
    assert concept.value == "100-105"


def test_fair_value_gap_neutral_when_no_gap():
    closes = np.array([100.0, 100.5, 101.0, 100.8, 101.2])
    highs = closes + 0.5
    lows = closes - 0.5
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Fair Value Gaps"].status == "NEUTRAL"


def test_liquidity_zones_bullish_when_high_volume_band_below_price():
    n = 30
    closes = np.linspace(100, 130, n)
    highs = closes + 1
    lows = closes - 1
    volumes = np.ones(n)
    volumes[:10] = 50.0  # heavy volume traded down near 100-105, well below the current price of ~130
    by_name = _by_name(analyze_smart_money(closes, highs, lows, volumes=volumes))

    assert by_name["Liquidity Zones"].status == "BULLISH"


def test_liquidity_zones_neutral_without_volume():
    closes = np.array([100.0] * 15)
    highs = closes + 1
    lows = closes - 1
    volumes = np.zeros(15)
    by_name = _by_name(analyze_smart_money(closes, highs, lows, volumes=volumes))

    assert by_name["Liquidity Zones"].status == "NEUTRAL"


def test_liquidity_sweep_bearish_when_wick_above_swing_high_then_rejected():
    highs = np.array([100, 100, 100, 106, 100, 100, 100, 100, 100, 100, 110.0])
    lows = highs - 2
    closes = highs - 1.5  # last candle wicks to 110 but closes at 108.5, below the prior swing high of 106...
    closes[-1] = 104.0  # closes back below the prior swing high of 106
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Liquidity Sweep"].status == "BEARISH"


def test_liquidity_sweep_neutral_without_wick_rejection():
    closes = np.array([100.0 + i for i in range(15)])
    highs = closes + 0.5
    lows = closes - 0.5
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    assert by_name["Liquidity Sweep"].status == "NEUTRAL"
