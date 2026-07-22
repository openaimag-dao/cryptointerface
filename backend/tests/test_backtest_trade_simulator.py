from app.ai_engine.decision_engine import AIDecision
from app.ai_engine.risk_engine import RiskPlan
from app.backtesting.models.config import TradeSimulatorConfig
from app.backtesting.trade_simulator import TradeSimulator
from app.schemas.candle import Candle


def _candle(time: int, open_: float, high: float, low: float, close: float) -> Candle:
    return Candle(time=time, open=open_, high=high, low=low, close=close, volume=100.0)


def _decision(direction: str, entry: float, stop: float, tp1: float) -> AIDecision:
    risk = None
    if direction != "WAIT":
        risk_per_unit = abs(entry - stop)
        reward = abs(tp1 - entry)
        risk = RiskPlan(
            direction=direction,
            entry=entry,
            stop=stop,
            tp1=tp1,
            tp2=tp1,
            tp3=tp1,
            risk_per_unit=risk_per_unit,
            risk_reward_tp1=reward / risk_per_unit if risk_per_unit else 0.0,
            risk_reward_tp2=0.0,
            risk_reward_tp3=0.0,
        )
    return AIDecision(
        symbol="TESTUSDT",
        interval="1h",
        timestamp=0,
        market_score=60.0,
        confidence=55.0,
        direction=direction,
        reasons=[],
        factors={},
        weights={},
        risk=risk,
    )


def _config(**overrides) -> TradeSimulatorConfig:
    base = {"initial_balance": 10_000.0, "commission_bps": 0.0, "slippage_bps": 0.0, "risk_per_trade_percent": 1.0}
    base.update(overrides)
    return TradeSimulatorConfig(**base)


def test_no_position_opened_on_wait_decision():
    sim = TradeSimulator(_config())
    bar = _candle(0, 100.0, 101.0, 99.0, 100.0)
    sim.process_bar("TESTUSDT", bar, _decision("WAIT", 100.0, 98.0, 103.0), is_last_bar=False)
    assert sim.position is None
    assert sim.closed_trades == []


def test_long_position_opens_and_hits_take_profit():
    sim = TradeSimulator(_config())
    entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)
    assert sim.position is not None
    assert sim.position.direction == "LONG"

    tp_bar = _candle(3600, 100.0, 104.0, 100.0, 103.5)
    sim.process_bar("TESTUSDT", tp_bar, None, is_last_bar=False)

    assert sim.position is None
    assert len(sim.closed_trades) == 1
    trade = sim.closed_trades[0]
    assert trade.exit_reason == "TP1"
    assert trade.exit_price == 103.0
    assert trade.pnl > 0


def test_long_position_stop_loss_hit():
    sim = TradeSimulator(_config())
    entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)

    sl_bar = _candle(3600, 100.0, 100.5, 97.0, 97.5)
    sim.process_bar("TESTUSDT", sl_bar, None, is_last_bar=False)

    assert len(sim.closed_trades) == 1
    trade = sim.closed_trades[0]
    assert trade.exit_reason == "SL"
    assert trade.exit_price == 98.0
    assert trade.pnl < 0


def test_entry_bar_itself_never_checked_for_exit_same_bar():
    """The bar whose decision opened a position must never be re-checked
    for exit against its own high/low — no look-ahead within one bar."""
    sim = TradeSimulator(_config())
    # This single bar's range would hit both the stop AND tp1 for a LONG
    # entered at 100 -- if the simulator incorrectly checked exit against
    # the entry bar itself, a trade would close immediately.
    entry_bar = _candle(0, 100.0, 110.0, 90.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)

    assert sim.position is not None
    assert sim.closed_trades == []


def test_same_bar_stop_and_tp_conflict_stop_wins():
    sim = TradeSimulator(_config())
    entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)

    conflict_bar = _candle(3600, 100.0, 105.0, 95.0, 100.0)  # touches both stop and tp1
    sim.process_bar("TESTUSDT", conflict_bar, None, is_last_bar=False)

    assert len(sim.closed_trades) == 1
    assert sim.closed_trades[0].exit_reason == "SL"


def test_short_position_take_profit_and_stop():
    sim = TradeSimulator(_config())
    entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("SHORT", entry=100.0, stop=102.0, tp1=97.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)
    assert sim.position.direction == "SHORT"

    tp_bar = _candle(3600, 100.0, 100.5, 96.0, 96.5)
    sim.process_bar("TESTUSDT", tp_bar, None, is_last_bar=False)

    assert sim.closed_trades[0].exit_reason == "TP1"
    assert sim.closed_trades[0].pnl > 0


def test_force_close_at_last_bar_uses_close_price():
    sim = TradeSimulator(_config())
    entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=90.0, tp1=120.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)

    last_bar = _candle(3600, 100.0, 101.0, 99.0, 100.5)
    sim.process_bar("TESTUSDT", last_bar, None, is_last_bar=True)

    assert sim.position is None
    assert len(sim.closed_trades) == 1
    trade = sim.closed_trades[0]
    assert trade.exit_reason == "END_OF_DATA"
    assert trade.exit_price == 100.5


def test_no_new_position_opened_on_last_bar():
    sim = TradeSimulator(_config())
    bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
    sim.process_bar("TESTUSDT", bar, decision, is_last_bar=True)
    assert sim.position is None
    assert sim.closed_trades == []


def test_commission_and_slippage_reduce_pnl():
    sim_no_cost = TradeSimulator(_config(commission_bps=0.0, slippage_bps=0.0))
    sim_with_cost = TradeSimulator(_config(commission_bps=10.0, slippage_bps=5.0))

    for sim in (sim_no_cost, sim_with_cost):
        entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
        decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
        sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)
        tp_bar = _candle(3600, 100.0, 104.0, 100.0, 103.5)
        sim.process_bar("TESTUSDT", tp_bar, None, is_last_bar=False)

    assert sim_with_cost.closed_trades[0].pnl < sim_no_cost.closed_trades[0].pnl


def test_one_position_at_a_time_no_new_entry_while_holding():
    sim = TradeSimulator(_config())
    entry_bar = _candle(0, 100.0, 100.0, 100.0, 100.0)
    decision = _decision("LONG", entry=100.0, stop=98.0, tp1=103.0)
    sim.process_bar("TESTUSDT", entry_bar, decision, is_last_bar=False)
    first_position = sim.position

    still_holding_bar = _candle(3600, 100.0, 101.0, 99.5, 100.5)
    another_decision = _decision("LONG", entry=100.5, stop=99.0, tp1=105.0)
    sim.process_bar("TESTUSDT", still_holding_bar, another_decision, is_last_bar=False)

    assert sim.position is first_position
