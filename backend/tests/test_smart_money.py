import numpy as np

from app.ai_engine.smart_money import analyze_smart_money

NOT_YET_IMPLEMENTED_NAMES = {
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
    assert len({c.name for c in concepts}) == 8


def test_five_concepts_are_not_yet_implemented():
    closes = np.array([100.0 + i for i in range(20)])
    highs = closes + 1
    lows = closes - 1
    by_name = _by_name(analyze_smart_money(closes, highs, lows))

    for name in NOT_YET_IMPLEMENTED_NAMES:
        assert by_name[name].status == "NOT_YET_IMPLEMENTED"
        assert by_name[name].value is None
        assert by_name[name].explanation


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
