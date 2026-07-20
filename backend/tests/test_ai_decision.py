import numpy as np

from app.ai_engine.decision_engine import MIN_CONFIDENCE_FOR_ACTION, analyze_market, decide_direction
from app.ai_engine.market_context import MarketContext
from app.schemas.candle import Candle


def test_decide_direction_market_wait_is_always_wait():
    assert decide_direction("WAIT", 100.0) == "WAIT"
    assert decide_direction("WAIT", 0.0) == "WAIT"


def test_decide_direction_downgrades_to_wait_below_confidence_floor():
    assert decide_direction("LONG", MIN_CONFIDENCE_FOR_ACTION - 0.01) == "WAIT"
    assert decide_direction("SHORT", MIN_CONFIDENCE_FOR_ACTION - 0.01) == "WAIT"


def test_decide_direction_passes_through_when_confident_enough():
    assert decide_direction("LONG", MIN_CONFIDENCE_FOR_ACTION) == "LONG"
    assert decide_direction("SHORT", MIN_CONFIDENCE_FOR_ACTION) == "SHORT"
    assert decide_direction("LONG", 100.0) == "LONG"


def test_decide_direction_only_ever_returns_one_of_three_values():
    for market_direction in ("LONG", "SHORT", "WAIT"):
        for confidence in (0.0, 10.0, 44.9, 45.0, 60.0, 100.0):
            assert decide_direction(market_direction, confidence) in ("LONG", "SHORT", "WAIT")


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


def test_analyze_market_uptrend_produces_long_with_min_five_reasons_and_risk_plan():
    closes = np.linspace(100, 160, 300) + np.sin(np.linspace(0, 20, 300)) * 0.5
    decision = analyze_market(_ctx(closes))

    assert decision.direction in ("LONG", "SHORT", "WAIT")
    assert len(decision.reasons) >= 5
    if decision.direction == "WAIT":
        assert decision.risk is None
    else:
        assert decision.risk is not None
        assert decision.risk.direction == decision.direction


def test_analyze_market_choppy_series_tends_toward_wait_and_has_no_risk_plan():
    rng = np.random.default_rng(9)
    closes = 100 + rng.normal(0, 0.3, 300)
    decision = analyze_market(_ctx(closes))

    assert decision.direction == "WAIT"
    assert decision.risk is None


def test_analyze_market_deterministic_same_input_same_output():
    closes = np.linspace(100, 150, 300) + np.sin(np.linspace(0, 15, 300)) * 0.4
    ctx = _ctx(closes)

    first = analyze_market(ctx)
    second = analyze_market(ctx)

    assert first.market_score == second.market_score
    assert first.confidence == second.confidence
    assert first.direction == second.direction
    assert first.reasons == second.reasons


def test_analyze_market_score_and_confidence_are_bounded():
    rng = np.random.default_rng(42)
    closes = 100 + np.cumsum(rng.normal(0, 1, 300))
    decision = analyze_market(_ctx(closes))

    assert 0.0 <= decision.market_score <= 100.0
    assert 0.0 <= decision.confidence <= 100.0
