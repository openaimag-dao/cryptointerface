"""Trade Simulator — turns a stream of (bar, Decision Engine output) pairs
into simulated fills.

**No look-ahead, by construction**: a position opened from bar `i`'s
decision (which only knows candles up to and including bar `i`'s close —
see `strategy_runner.py`) is never checked for an exit against bar `i`'s
own high/low. By the time the decision is known, bar `i` has already
closed — there is no more of it left to trade against. Monitoring starts
at bar `i + 1`, using each subsequent bar's high/low the same way a
resting stop/limit order would actually behave.

**Same-bar SL/TP conflict**: if a single bar's range touches both the
stop and TP1, there's no way to know from OHLC data alone which was hit
first intrabar — this simulator conservatively assumes the stop fills
first. This is the standard conservative convention for bar-resolution
backtesting (never assume the best case when the data can't tell you).

**Mark-to-close only**: balance only changes when a trade closes, not
bar-by-bar on unrealized P&L. See `risk_metrics.py`'s docstring for why
Sharpe/Sortino are computed from trade returns rather than a bar-level
equity series as a result.

**One position at a time**: a new entry is only ever considered while
flat. `TradeSimulatorConfig.allow_concurrent_positions` exists for a
future multi-position model but isn't implemented — see
`backend/README.md`'s Limitations section.
"""

from app.ai_engine.decision_engine import AIDecision
from app.backtesting.models.config import TradeSimulatorConfig
from app.backtesting.models.trade import ClosedTrade, OpenPosition
from app.schemas.candle import Candle

BPS = 10_000.0


class TradeSimulator:
    def __init__(self, config: TradeSimulatorConfig) -> None:
        self.config = config
        self.balance = config.initial_balance
        self.position: OpenPosition | None = None
        self.closed_trades: list[ClosedTrade] = []

    def process_bar(self, symbol: str, bar: Candle, decision: AIDecision | None, is_last_bar: bool) -> None:
        if self.position is not None:
            self._check_exit(symbol, bar)

        if self.position is None and not is_last_bar and decision is not None:
            self._maybe_open(bar, decision)

        if self.position is not None and is_last_bar:
            self._force_close(symbol, bar)

    # -- entry -----------------------------------------------------------

    def _maybe_open(self, bar: Candle, decision: AIDecision) -> None:
        if decision.direction == "WAIT" or decision.risk is None:
            return

        risk = decision.risk
        risk_per_unit = abs(risk.entry - risk.stop)
        if risk_per_unit <= 0:
            return

        risk_dollars = self.balance * (self.config.risk_per_trade_percent / 100.0)
        quantity = risk_dollars / risk_per_unit
        if quantity <= 0:
            return

        self.position = OpenPosition(
            direction=decision.direction,  # type: ignore[arg-type]  # WAIT already excluded above
            entry_time=bar.time,
            entry_price=risk.entry,
            stop=risk.stop,
            tp1=risk.tp1,
            quantity=quantity,
            decision_score=decision.market_score,
            confidence=decision.confidence,
            planned_risk_reward=risk.risk_reward_tp1,
        )

    # -- exit --------------------------------------------------------------

    def _check_exit(self, symbol: str, bar: Candle) -> None:
        position = self.position
        assert position is not None

        if position.direction == "LONG":
            hit_stop = bar.low <= position.stop
            hit_tp = bar.high >= position.tp1
        else:
            hit_stop = bar.high >= position.stop
            hit_tp = bar.low <= position.tp1

        if hit_stop:
            self._close(symbol, bar.time, position.stop, "SL")
        elif hit_tp:
            self._close(symbol, bar.time, position.tp1, "TP1")

    def _force_close(self, symbol: str, bar: Candle) -> None:
        self._close(symbol, bar.time, bar.close, "END_OF_DATA")

    def _close(self, symbol: str, exit_time: int, exit_price: float, reason: str) -> None:
        position = self.position
        assert position is not None
        self.position = None

        slippage = self.config.slippage_bps / BPS
        commission_rate = self.config.commission_bps / BPS

        if position.direction == "LONG":
            fill_entry = position.entry_price * (1 + slippage)
            fill_exit = exit_price * (1 - slippage)
            gross_pnl = (fill_exit - fill_entry) * position.quantity
        else:
            fill_entry = position.entry_price * (1 - slippage)
            fill_exit = exit_price * (1 + slippage)
            gross_pnl = (fill_entry - fill_exit) * position.quantity

        notional = (fill_entry + fill_exit) * position.quantity
        commission = notional * commission_rate
        net_pnl = gross_pnl - commission

        balance_at_entry = self.balance
        self.balance += net_pnl
        pnl_percent = (net_pnl / balance_at_entry * 100.0) if balance_at_entry > 0 else 0.0

        self.closed_trades.append(
            ClosedTrade(
                symbol=symbol,
                direction=position.direction,
                entry_time=position.entry_time,
                entry_price=position.entry_price,
                exit_time=exit_time,
                exit_price=exit_price,
                quantity=position.quantity,
                pnl=net_pnl,
                pnl_percent=pnl_percent,
                exit_reason=reason,  # type: ignore[arg-type]
                duration_seconds=max(0, exit_time - position.entry_time),
                decision_score=position.decision_score,
                confidence=position.confidence,
                planned_risk_reward=position.planned_risk_reward,
            )
        )
