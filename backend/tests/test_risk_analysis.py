import numpy as np

from app.ai_engine.decision_engine import analyze_market
from app.ai_engine.market_context import MarketContext
from app.ai_engine.risk_analysis import (
    MAX_RECOMMENDED_LEVERAGE,
    MIN_RECOMMENDED_LEVERAGE,
    _risk_level,
    analyze_risk,
)
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


def test_risk_level_buckets():
    assert _risk_level(None) == "MODERATE"
    assert _risk_level(0.5) == "LOW"
    assert _risk_level(2.0) == "MODERATE"
    assert _risk_level(4.0) == "HIGH"
    assert _risk_level(10.0) == "EXTREME"


def test_analyze_risk_returns_bounded_leverage_and_valid_risk_level():
    closes = np.linspace(100, 160, 300) + np.sin(np.linspace(0, 20, 300)) * 0.5
    ctx = _ctx(closes)
    decision = analyze_market(ctx)

    risk = analyze_risk(ctx, decision)

    assert MIN_RECOMMENDED_LEVERAGE <= risk.max_recommended_leverage <= MAX_RECOMMENDED_LEVERAGE
    assert risk.risk_level in ("LOW", "MODERATE", "HIGH", "EXTREME")
    assert risk.atr is not None
    assert risk.atr_risk_pct is not None
    assert risk.drawdown_risk_pct is not None
    assert risk.drawdown_risk_pct > 0.0


def test_analyze_risk_higher_volatility_lowers_recommended_leverage():
    calm_closes = np.linspace(100, 110, 300)
    volatile_closes = 100 + np.cumsum(np.random.default_rng(3).normal(0, 3, 300))

    calm_ctx = _ctx(calm_closes)
    volatile_ctx = _ctx(volatile_closes)

    calm_risk = analyze_risk(calm_ctx, analyze_market(calm_ctx))
    volatile_risk = analyze_risk(volatile_ctx, analyze_market(volatile_ctx))

    assert volatile_risk.atr_risk_pct > calm_risk.atr_risk_pct
    assert volatile_risk.max_recommended_leverage <= calm_risk.max_recommended_leverage


def test_analyze_risk_deterministic_same_input_same_output():
    closes = np.linspace(100, 150, 300) + np.sin(np.linspace(0, 15, 300)) * 0.4
    ctx = _ctx(closes)
    decision = analyze_market(ctx)

    first = analyze_risk(ctx, decision)
    second = analyze_risk(ctx, decision)

    assert first == second


def test_analyze_risk_uses_risk_plan_drawdown_when_direction_is_active():
    closes = np.linspace(100, 200, 300)
    ctx = _ctx(closes)
    decision = analyze_market(ctx)
    risk = analyze_risk(ctx, decision)

    if decision.risk is not None:
        expected_pct = decision.risk.risk_per_unit / decision.risk.entry * 100.0
        assert round(risk.drawdown_risk_pct, 2) == round(expected_pct, 2)
