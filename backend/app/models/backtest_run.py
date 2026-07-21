from sqlalchemy import JSON, BigInteger, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class BacktestRun(Base, IdMixin, CreatedAtMixin):
    """One backtest execution: its request parameters, status, and timing.
    Trades (`backtest_trades`), computed metrics (`backtest_metrics`), and
    the equity curve (`equity_curve`) all reference this row's `id`.

    `status` moves PENDING -> RUNNING -> COMPLETED | FAILED; `error_message`
    is set only on FAILED (insufficient history, bad parameters, or a
    computation error — see `app/backtesting/utils/errors.py`).
    """

    __tablename__ = "backtest_runs"
    __table_args__ = (Index("ix_backtest_runs_symbol_created_at", "symbol", "created_at"),)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[int] = mapped_column(BigInteger, nullable=False)  # unix seconds, first bar analyzed
    end_time: Mapped[int] = mapped_column(BigInteger, nullable=False)  # unix seconds, last bar analyzed
    strategy_version_id: Mapped[int] = mapped_column(ForeignKey("strategy_versions.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    initial_balance: Mapped[float] = mapped_column(Float, nullable=False, default=10_000.0)
    commission_bps: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    slippage_bps: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    # Trade Simulator config snapshot not already covered by the columns
    # above — position sizing, and the trailing-stop/break-even/partial-TP
    # architecture flags (see app/backtesting/trade_simulator.py).
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # unix seconds
    completed_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # unix seconds
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
