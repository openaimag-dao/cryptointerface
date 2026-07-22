import numpy as np

from app.backtesting.strategy_runner import iter_decisions
from app.models.funding import FundingRate
from app.models.open_interest import OpenInterest
from app.schemas.candle import Candle


def _candles(n: int, start_time: int = 0, step: int = 3600) -> list[Candle]:
    closes = 100 + np.cumsum(np.sin(np.linspace(0, 20, n)) * 0.3 + 0.05)
    return [
        Candle(
            time=start_time + i * step,
            open=float(closes[i]),
            high=float(closes[i]) + 0.5,
            low=float(closes[i]) - 0.5,
            close=float(closes[i]),
            volume=1000.0,
        )
        for i in range(n)
    ]


def test_iter_decisions_yields_none_during_warmup_then_real_decisions():
    candles = _candles(20)
    results = list(iter_decisions("TESTUSDT", "1h", candles, [], [], candle_lookback=5))

    assert len(results) == 20
    for r in results[:4]:
        assert r.decision is None
    for r in results[4:]:
        assert r.decision is not None
        assert r.decision.symbol == "TESTUSDT"
        assert r.decision.interval == "1h"


def test_iter_decisions_deterministic_same_input_same_output():
    candles = _candles(280)
    first = list(iter_decisions("TESTUSDT", "1h", candles, [], []))
    second = list(iter_decisions("TESTUSDT", "1h", candles, [], []))

    for a, b in zip(first, second, strict=True):
        if a.decision is None:
            assert b.decision is None
        else:
            assert a.decision.market_score == b.decision.market_score
            assert a.decision.direction == b.decision.direction
            assert a.decision.confidence == b.decision.confidence


def test_iter_decisions_no_look_ahead_truncating_future_bars_does_not_change_past_decisions():
    candles = _candles(300)
    full = list(iter_decisions("TESTUSDT", "1h", candles, [], []))
    truncated = list(iter_decisions("TESTUSDT", "1h", candles[:-50], [], []))

    for a, b in zip(full[: len(truncated)], truncated, strict=True):
        if a.decision is None:
            assert b.decision is None
            continue
        assert a.decision.market_score == b.decision.market_score
        assert a.decision.direction == b.decision.direction
        assert a.decision.confidence == b.decision.confidence
        assert a.decision.reasons == b.decision.reasons


def test_iter_decisions_never_passes_future_funding_or_oi_to_a_bar(monkeypatch):
    candles = _candles(20)
    funding_history = [
        FundingRate(symbol="TESTUSDT", funding_rate=0.0001, mark_price=100.0, funding_time=candles[i].time)
        for i in (2, 6, 10, 14, 18)
    ]
    oi_history = [
        OpenInterest(symbol="TESTUSDT", open_interest=1000.0, open_interest_value=100_000.0, timestamp=candles[i].time)
        for i in (3, 7, 11, 15, 19)
    ]

    captured: list[tuple[int, list[FundingRate], list[OpenInterest]]] = []

    import app.backtesting.strategy_runner as strategy_runner_module

    original = strategy_runner_module.build_market_context_from_data

    def spy(symbol, interval, window, funding_window, oi_window, **kwargs):
        captured.append((window[-1].time, list(funding_window), list(oi_window)))
        return original(symbol, interval, window, funding_window, oi_window, **kwargs)

    monkeypatch.setattr(strategy_runner_module, "build_market_context_from_data", spy)

    list(iter_decisions("TESTUSDT", "1h", candles, funding_history, oi_history, candle_lookback=5))

    assert captured  # sanity: the spy was actually invoked
    for bar_time, funding_window, oi_window in captured:
        assert all(f.funding_time <= bar_time for f in funding_window)
        assert all(o.timestamp <= bar_time for o in oi_window)
