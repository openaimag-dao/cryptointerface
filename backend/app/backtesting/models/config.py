"""Internal (non-DB, non-API) configuration dataclasses the engine
computes with. Distinct from `app/models/backtest_run.py` (the persisted
row) and `app/schemas/backtest.py` (the HTTP request/response shape) —
this is the in-memory object strategy_runner/trade_simulator actually
pass around, same separation `app/ai_engine/types.py` keeps for the
Decision Engine.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TradeSimulatorConfig:
    """All Trade Simulator behavior is driven by this — nothing is a
    hardcoded constant inside `trade_simulator.py` itself, so every run
    can be reproduced exactly from its stored config (see `BacktestRun.config`).
    """

    initial_balance: float = 10_000.0
    commission_bps: float = 4.0  # round-trip commission, basis points of notional
    slippage_bps: float = 2.0  # applied against the fill price, both entry and exit
    # Risk-based position sizing: quantity is chosen so that
    # (entry - stop) * quantity == balance * risk_per_trade_percent / 100.
    # A single flat "bet size" isn't realistic for a strategy whose stop
    # distance varies bar to bar (it's ATR/structure-based, see
    # app/ai_engine/risk_engine.py) — sizing by risk keeps every trade's
    # downside comparable in balance terms.
    risk_per_trade_percent: float = 1.0
    # Only one open position at a time — the simplest, least-ambiguous
    # model, and the one the spec's Trade List (one row per trade) assumes.
    allow_concurrent_positions: bool = False

    # --- Architecture only (see backend/README.md's Limitations section) ---
    # Config is accepted and stored for forward-compatibility, but the
    # bar-by-bar fill loop in trade_simulator.py does not yet act on these:
    # every trade still exits at a static TP1 or SL set at entry.
    trailing_stop_enabled: bool = False
    trailing_stop_atr_multiplier: float | None = None
    break_even_enabled: bool = False
    break_even_trigger_r: float | None = None
    partial_take_profit_enabled: bool = False
    # (r_multiple, fraction_of_position_to_close) pairs, e.g. [(1.5, 0.5)]
    # would close half the position at TP1.
    partial_take_profit_levels: tuple[tuple[float, float], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BacktestConfig:
    symbol: str
    timeframe: str
    period_days: int
    strategy_version_name: str
    simulator: TradeSimulatorConfig = field(default_factory=TradeSimulatorConfig)
