from dataclasses import dataclass
from typing import Literal

Direction = Literal["LONG", "SHORT"]
ExitReason = Literal["TP1", "SL", "END_OF_DATA"]


@dataclass
class OpenPosition:
    """A position the Trade Simulator is currently holding — mutable
    (`trade_simulator.py` updates it bar by bar), unlike everything else
    in this module."""

    direction: Direction
    entry_time: int
    entry_price: float
    stop: float
    tp1: float
    quantity: float
    decision_score: float
    confidence: float
    planned_risk_reward: float  # RiskPlan.risk_reward_tp1 at entry, see app/ai_engine/risk_engine.py

    @property
    def risk_per_unit(self) -> float:
        return abs(self.entry_price - self.stop)


@dataclass(frozen=True)
class ClosedTrade:
    """One finished trade — what `backtest_trades` rows and the API's
    Trade List are built from."""

    symbol: str
    direction: Direction
    entry_time: int
    entry_price: float
    exit_time: int
    exit_price: float
    quantity: float
    pnl: float  # net of commission + slippage
    pnl_percent: float  # relative to balance at entry
    exit_reason: ExitReason
    duration_seconds: int
    decision_score: float
    confidence: float
    planned_risk_reward: float
