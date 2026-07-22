import pytest

from app.ai_engine.decision_engine import AIDecision
from app.ai_engine.risk_engine import RiskPlan
from app.services.ai_repository import insert_ai_analysis
from app.services.binance.rest_client import KlineData
from app.services.history_service import get_history_summary
from app.services.market_repository import upsert_candle

BASE_TIME_MS = 1_700_000_000_000
BASE_TIME_S = BASE_TIME_MS // 1000


def _decision(*, time: int, direction: str, entry=None, stop=None, tp1=None) -> AIDecision:
    risk = None
    if direction != "WAIT" and entry is not None:
        risk = RiskPlan(
            direction=direction,
            entry=entry,
            stop=stop,
            tp1=tp1,
            tp2=tp1,
            tp3=tp1,
            risk_per_unit=abs(entry - stop),
            risk_reward_tp1=1.0,
            risk_reward_tp2=1.0,
            risk_reward_tp3=1.0,
        )
    return AIDecision(
        symbol="TESTUSDT",
        interval="1h",
        timestamp=time,
        market_score=60.0 if direction == "LONG" else 40.0 if direction == "SHORT" else 50.0,
        confidence=70.0,
        direction=direction,
        reasons=["synthetic test reason"],
        factors={},
        weights={},
        risk=risk,
    )


async def _seed_candle(db_session, symbol: str, time_s: int, price: float, high=None, low=None) -> None:
    kline = KlineData(
        open_time=time_s * 1000,
        close_time=time_s * 1000 + 3_599_999,
        open=price,
        high=high if high is not None else price,
        low=low if low is not None else price,
        close=price,
        volume=1000.0,
        quote_volume=100_000.0,
        trades=10,
    )
    await upsert_candle(db_session, symbol, "1h", kline, is_closed=True)


@pytest.mark.asyncio
async def test_get_history_summary_empty_when_no_analysis_persisted(db_session):
    summary = await get_history_summary(db_session, "NOHISTORYUSDT", "1h")

    assert summary.signals == []
    assert summary.win_rate is None
    assert summary.avg_win_pnl_percent is None
    assert summary.avg_loss_pnl_percent is None


@pytest.mark.asyncio
async def test_get_history_summary_wait_decisions_are_no_trade(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, direction="WAIT"))

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    assert len(summary.signals) == 1
    assert summary.signals[0].outcome == "NO_TRADE"
    assert summary.win_rate is None


@pytest.mark.asyncio
async def test_get_history_summary_resolves_win_when_tp1_hit_first(db_session):
    decision = _decision(time=BASE_TIME_S, direction="LONG", entry=100.0, stop=90.0, tp1=110.0)
    await insert_ai_analysis(db_session, decision)

    # Bar after the signal: high reaches tp1 (110), low never touches stop (90).
    await _seed_candle(db_session, "TESTUSDT", BASE_TIME_S + 3600, price=105.0, high=112.0, low=104.0)

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    assert len(summary.signals) == 1
    assert summary.signals[0].outcome == "WIN"
    assert summary.signals[0].pnl_percent == pytest.approx(10.0)
    assert summary.win_rate == 100.0
    assert summary.avg_win_pnl_percent == pytest.approx(10.0)
    assert summary.avg_loss_pnl_percent is None


@pytest.mark.asyncio
async def test_get_history_summary_resolves_loss_when_stop_hit_first(db_session):
    decision = _decision(time=BASE_TIME_S, direction="LONG", entry=100.0, stop=90.0, tp1=110.0)
    await insert_ai_analysis(db_session, decision)

    await _seed_candle(db_session, "TESTUSDT", BASE_TIME_S + 3600, price=92.0, high=95.0, low=88.0)

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    assert summary.signals[0].outcome == "LOSS"
    assert summary.signals[0].pnl_percent == pytest.approx(-10.0)
    assert summary.win_rate == 0.0
    assert summary.avg_loss_pnl_percent == pytest.approx(-10.0)


@pytest.mark.asyncio
async def test_get_history_summary_same_bar_hits_both_stop_wins(db_session):
    decision = _decision(time=BASE_TIME_S, direction="LONG", entry=100.0, stop=90.0, tp1=110.0)
    await insert_ai_analysis(db_session, decision)

    # Single bar's range covers both stop and tp1 -> conservative rule: stop wins.
    await _seed_candle(db_session, "TESTUSDT", BASE_TIME_S + 3600, price=100.0, high=115.0, low=85.0)

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    assert summary.signals[0].outcome == "LOSS"


@pytest.mark.asyncio
async def test_get_history_summary_open_when_neither_level_hit_within_horizon(db_session):
    decision = _decision(time=BASE_TIME_S, direction="LONG", entry=100.0, stop=90.0, tp1=110.0)
    await insert_ai_analysis(db_session, decision)

    await _seed_candle(db_session, "TESTUSDT", BASE_TIME_S + 3600, price=101.0, high=103.0, low=99.0)

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    assert summary.signals[0].outcome == "OPEN"
    assert summary.signals[0].pnl_percent is None
    assert summary.win_rate is None


@pytest.mark.asyncio
async def test_get_history_summary_short_win(db_session):
    decision = _decision(time=BASE_TIME_S, direction="SHORT", entry=100.0, stop=110.0, tp1=90.0)
    await insert_ai_analysis(db_session, decision)

    await _seed_candle(db_session, "TESTUSDT", BASE_TIME_S + 3600, price=95.0, high=96.0, low=88.0)

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    assert summary.signals[0].outcome == "WIN"
    assert summary.signals[0].pnl_percent == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_get_history_summary_score_and_confidence_history_ordered_ascending(db_session):
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S, direction="WAIT"))
    await insert_ai_analysis(db_session, _decision(time=BASE_TIME_S + 3600, direction="WAIT"))

    summary = await get_history_summary(db_session, "TESTUSDT", "1h")

    times = [t for t, _ in summary.score_history]
    assert times == sorted(times)
