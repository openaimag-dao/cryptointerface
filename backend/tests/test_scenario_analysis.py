import numpy as np

from app.ai_engine.decision_engine import analyze_market
from app.ai_engine.market_context import MarketContext
from app.ai_engine.scenario_analysis import _scenario_probabilities, analyze_scenarios
from app.schemas.candle import Candle


def _ctx(closes: np.ndarray) -> MarketContext:
    highs = closes + 0.5
    lows = closes - 0.5
    volumes = np.full(len(closes), 1000.0)
    candles = [
        Candle(
            time=i,
            open=float(closes[i]),
            high=float(highs[i]),
            low=float(lows[i]),
            close=float(closes[i]),
            volume=1000.0,
        )
        for i in range(len(closes))
    ]
    return MarketContext(
        symbol="TESTUSDT",
        interval="1h",
        candles=candles,
        opens=closes,
        highs=highs,
        lows=lows,
        closes=closes,
        volumes=volumes,
        funding_history=[],
        oi_history=[],
    )


def test_scenario_probabilities_always_sum_to_100():
    for market_score in (0.0, 25.0, 50.0, 65.0, 100.0):
        for confidence in (0.0, 30.0, 55.0, 100.0):
            bullish, neutral, bearish = _scenario_probabilities(market_score, confidence)
            assert round(bullish + neutral + bearish, 6) == 100.0
            assert bullish >= 0.0
            assert neutral >= 0.0
            assert bearish >= 0.0


def test_scenario_probabilities_zero_confidence_is_all_neutral():
    bullish, neutral, bearish = _scenario_probabilities(90.0, 0.0)
    assert neutral == 100.0
    assert bullish == 0.0
    assert bearish == 0.0


def test_scenario_probabilities_full_confidence_bullish_score_has_no_bearish_mass():
    bullish, neutral, bearish = _scenario_probabilities(100.0, 100.0)
    assert neutral == 0.0
    assert bearish == 0.0
    assert bullish == 100.0


def test_scenario_probabilities_full_confidence_bearish_score_has_no_bullish_mass():
    bullish, neutral, bearish = _scenario_probabilities(0.0, 100.0)
    assert neutral == 0.0
    assert bullish == 0.0
    assert bearish == 100.0


def test_scenario_probabilities_neutral_score_splits_evenly():
    bullish, neutral, bearish = _scenario_probabilities(50.0, 80.0)
    assert bullish == bearish
    assert round(bullish + bearish, 6) == 80.0
    assert neutral == 20.0


def test_analyze_scenarios_returns_three_labeled_scenarios_summing_to_100():
    closes = np.linspace(100, 160, 300) + np.sin(np.linspace(0, 20, 300)) * 0.5
    ctx = _ctx(closes)
    decision = analyze_market(ctx)

    scenarios = analyze_scenarios(ctx, decision)

    assert {s.label for s in scenarios} == {"BULLISH", "NEUTRAL", "BEARISH"}
    assert round(sum(s.probability for s in scenarios), 1) == 100.0
    for s in scenarios:
        assert len(s.conditions) >= 1


def test_analyze_scenarios_deterministic_same_input_same_output():
    closes = np.linspace(100, 150, 300) + np.sin(np.linspace(0, 15, 300)) * 0.4
    ctx = _ctx(closes)
    decision = analyze_market(ctx)

    first = analyze_scenarios(ctx, decision)
    second = analyze_scenarios(ctx, decision)

    assert first == second


def test_analyze_scenarios_targets_are_ordered_around_price_for_directional_scenarios():
    closes = np.linspace(100, 160, 300) + np.sin(np.linspace(0, 20, 300)) * 0.5
    ctx = _ctx(closes)
    decision = analyze_market(ctx)
    price = ctx.last_close

    scenarios = {s.label: s for s in analyze_scenarios(ctx, decision)}

    bullish_targets = scenarios["BULLISH"].targets
    assert all(target >= price for target in bullish_targets)
    bearish_targets = scenarios["BEARISH"].targets
    assert all(target <= price for target in bearish_targets)
