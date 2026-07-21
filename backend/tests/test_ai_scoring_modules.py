from types import SimpleNamespace

import numpy as np

from app.ai_engine.scoring.funding import score_funding
from app.ai_engine.scoring.macro import score_macro
from app.ai_engine.scoring.momentum import score_momentum
from app.ai_engine.scoring.news import score_news
from app.ai_engine.scoring.oi import score_oi
from app.ai_engine.scoring.structure import score_structure
from app.ai_engine.scoring.volatility import score_volatility
from app.ai_engine.scoring.volume import score_volume
from app.ai_engine.types import MacroIndicatorReading, MacroSnapshot


def _uptrend(n: int = 300) -> np.ndarray:
    return np.linspace(100, 150, n) + np.sin(np.linspace(0, 15, n)) * 0.4


def test_momentum_score_bounded_and_deterministic():
    closes = _uptrend()
    first = score_momentum(closes)
    second = score_momentum(closes)

    assert 0.0 <= first.score <= 100.0
    assert first.direction in ("LONG", "SHORT", "WAIT")
    assert first.score == second.score
    assert first.reasons == second.reasons


def test_volatility_never_falls_back_to_misleading_insufficient_message_with_full_history():
    closes = _uptrend()
    highs = closes + 0.5
    lows = closes - 0.5
    factor = score_volatility(closes, highs, lows)

    assert not any(r.startswith("Insufficient candle history") for r in factor.reasons)
    assert len(factor.reasons) >= 1


def test_volatility_squeeze_detection_on_flat_series():
    closes = np.full(300, 100.0)
    highs = closes + 0.01
    lows = closes - 0.01
    factor = score_volatility(closes, highs, lows)

    assert factor.score == 50.0


def test_volume_score_bounded_and_deterministic():
    rng = np.random.default_rng(1)
    closes = _uptrend()
    highs = closes + 0.5
    lows = closes - 0.5
    volumes = rng.uniform(1000, 3000, len(closes))

    first = score_volume(closes, highs, lows, volumes)
    second = score_volume(closes, highs, lows, volumes)

    assert 0.0 <= first.score <= 100.0
    assert first.score == second.score


def test_structure_breakout_detected_above_resistance():
    # A well-formed swing high from oscillation, then a decisive ramp
    # above it — gives the swing detector a clean prior resistance level
    # to compare the breakout against.
    part1 = 100 + 5 * np.sin(np.linspace(0, 6 * np.pi, 250))
    part2 = np.linspace(part1[-1], 130, 50)
    closes = np.concatenate([part1, part2])
    highs = closes + 0.5
    lows = closes - 0.5
    factor = score_structure(closes, highs, lows)

    assert any("breakout" in r for r in factor.reasons)
    assert factor.direction == "LONG"


def test_funding_extreme_positive_is_contrarian_bearish():
    history = [SimpleNamespace(funding_rate=rate) for rate in (0.0001, 0.0003, 0.0006, 0.0009)]
    factor = score_funding(history)

    assert factor.direction == "SHORT"
    assert any("contrarian bearish" in r for r in factor.reasons)


def test_funding_extreme_negative_is_contrarian_bullish():
    history = [SimpleNamespace(funding_rate=rate) for rate in (-0.0001, -0.0004, -0.0007, -0.0009)]
    factor = score_funding(history)

    assert factor.direction == "LONG"
    assert any("contrarian bullish" in r for r in factor.reasons)


def test_funding_empty_history_is_neutral():
    factor = score_funding([])

    assert factor.score == 50.0
    assert factor.direction == "WAIT"


def test_oi_rising_with_price_confirms_bullish_trend():
    oi_history = [SimpleNamespace(open_interest=1000.0), SimpleNamespace(open_interest=1100.0)]
    closes = np.linspace(100, 110, 25)
    factor = score_oi(closes, oi_history)

    assert factor.direction == "LONG"
    assert any("new longs entering" in r for r in factor.reasons)


def test_oi_rising_with_falling_price_confirms_bearish_trend():
    oi_history = [SimpleNamespace(open_interest=1000.0), SimpleNamespace(open_interest=1100.0)]
    closes = np.linspace(110, 100, 25)
    factor = score_oi(closes, oi_history)

    assert factor.direction == "SHORT"
    assert any("new shorts entering" in r for r in factor.reasons)


def test_oi_insufficient_history_is_neutral():
    factor = score_oi(np.linspace(100, 110, 25), [])

    assert factor.score == 50.0
    assert factor.direction == "WAIT"


def test_macro_no_snapshot_is_neutral_and_labeled_as_stub():
    factor = score_macro(None)

    assert factor.score == 50.0
    assert factor.direction == "WAIT"
    assert factor.details["stub"] is True


def test_macro_bullish_snapshot_scores_above_neutral():
    snapshot = MacroSnapshot(
        dxy=MacroIndicatorReading(value=25.0, change_percent=-1.5),  # weaker dollar -> bullish
        nasdaq=MacroIndicatorReading(value=400.0, change_percent=2.0),  # risk-on -> bullish
        fear_greed=MacroIndicatorReading(value=80.0, change_percent=None),  # greed -> bullish
    )
    factor = score_macro(snapshot)

    assert factor.score > 50.0
    assert factor.direction in ("LONG", "WAIT")
    assert any("NASDAQ" in reason for reason in factor.reasons)
    assert any("DXY" in reason for reason in factor.reasons)


def test_macro_bearish_snapshot_scores_below_neutral():
    snapshot = MacroSnapshot(
        dxy=MacroIndicatorReading(value=25.0, change_percent=1.5),  # stronger dollar -> bearish
        nasdaq=MacroIndicatorReading(value=400.0, change_percent=-2.0),  # risk-off -> bearish
        vix=MacroIndicatorReading(value=15.0, change_percent=10.0),  # fear spiking -> bearish
        fear_greed=MacroIndicatorReading(value=15.0, change_percent=None),  # fear -> bearish
    )
    factor = score_macro(snapshot)

    assert factor.score < 50.0
    assert factor.direction in ("SHORT", "WAIT")


def test_macro_snapshot_with_no_moving_readings_stays_neutral():
    snapshot = MacroSnapshot(dxy=MacroIndicatorReading(value=25.0, change_percent=0.0))
    factor = score_macro(snapshot)

    assert factor.score == 50.0


def test_macro_deterministic_same_input_same_output():
    snapshot = MacroSnapshot(nasdaq=MacroIndicatorReading(value=400.0, change_percent=1.2))
    first = score_macro(snapshot)
    second = score_macro(snapshot)

    assert first.score == second.score
    assert first.reasons == second.reasons


def test_news_stub_is_neutral_and_labeled_as_stub():
    factor = score_news()

    assert factor.score == 50.0
    assert factor.direction == "WAIT"
    assert factor.details["stub"] is True
