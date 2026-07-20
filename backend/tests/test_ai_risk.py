import numpy as np
import pytest

from app.ai_engine.market_context import MarketContext
from app.ai_engine.risk_engine import compute_risk_plan
from app.ai_engine.types import make_factor_score
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


def _no_structure_factor():
    return make_factor_score("structure", 50.0, ["no levels found"], details={})


def test_wait_direction_returns_no_risk_plan():
    rng = np.random.default_rng(1)
    ctx = _ctx(100 + np.cumsum(rng.normal(0, 1, 300)))
    plan = compute_risk_plan("WAIT", ctx, _no_structure_factor())

    assert plan is None


def test_long_plan_has_sane_ordering_and_default_r_multiples():
    rng = np.random.default_rng(2)
    ctx = _ctx(np.linspace(100, 150, 300) + rng.normal(0, 1, 300))
    plan = compute_risk_plan("LONG", ctx, _no_structure_factor())

    assert plan is not None
    assert plan.stop < plan.entry < plan.tp1 < plan.tp2 < plan.tp3
    assert plan.risk_per_unit > 0
    assert plan.risk_reward_tp1 == pytest.approx(1.5)
    assert plan.risk_reward_tp2 == pytest.approx(2.5)
    assert plan.risk_reward_tp3 == pytest.approx(4.0)


def test_short_plan_has_sane_ordering_and_default_r_multiples():
    rng = np.random.default_rng(3)
    ctx = _ctx(np.linspace(150, 100, 300) + rng.normal(0, 1, 300))
    plan = compute_risk_plan("SHORT", ctx, _no_structure_factor())

    assert plan is not None
    assert plan.tp3 < plan.tp2 < plan.tp1 < plan.entry < plan.stop
    assert plan.risk_per_unit > 0
    assert plan.risk_reward_tp1 == pytest.approx(1.5)
    assert plan.risk_reward_tp2 == pytest.approx(2.5)
    assert plan.risk_reward_tp3 == pytest.approx(4.0)


def test_long_plan_uses_nearby_support_instead_of_pure_atr_stop():
    rng = np.random.default_rng(4)
    closes = np.linspace(100, 150, 300) + rng.normal(0, 0.5, 300)
    ctx = _ctx(closes)
    entry = ctx.last_close

    # A support level just a little below entry, well within the max ATR
    # multiple, should be used (with a small buffer) instead of the pure
    # ATR-multiple stop.
    close_support = entry - 1.0
    structure = make_factor_score("structure", 50.0, ["support nearby"], details={"nearest_support": close_support})
    plan = compute_risk_plan("LONG", ctx, structure)

    assert plan is not None
    assert plan.stop < close_support


def test_deterministic_same_input_same_output():
    rng = np.random.default_rng(5)
    ctx = _ctx(np.linspace(100, 150, 300) + rng.normal(0, 1, 300))
    factor = _no_structure_factor()

    first = compute_risk_plan("LONG", ctx, factor)
    second = compute_risk_plan("LONG", ctx, factor)

    assert first == second
