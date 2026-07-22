from sqlalchemy import BigInteger, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class BacktestTrade(Base, IdMixin, CreatedAtMixin):
    """One simulated trade from a backtest run (`app/backtesting/trade_simulator.py`).

    `decision_score`/`confidence` are the Decision Engine's own Market
    Score/Confidence at entry — the exact same numbers `/api/ai/*` would
    have shown a live user at that historical bar, letting the Trade List
    (Sprint 5 spec's "Decision Score"/"Confidence" columns) show precisely
    what the engine believed when it opened the trade.
    """

    __tablename__ = "backtest_trades"
    __table_args__ = (Index("ix_backtest_trades_run_entry_time", "backtest_run_id", "entry_time"),)

    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)  # LONG | SHORT
    entry_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float] = mapped_column(Float, nullable=False)  # net of commission + slippage
    pnl_percent: Mapped[float] = mapped_column(Float, nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(16), nullable=False)  # TP1 | SL | END_OF_DATA
    duration_seconds: Mapped[int] = mapped_column(BigInteger, nullable=False)
    decision_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    planned_risk_reward: Mapped[float] = mapped_column(Float, nullable=False)
