from sqlalchemy import BigInteger, Float, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class EquityCurvePoint(Base, IdMixin, CreatedAtMixin):
    """One point on a backtest run's equity curve. Not one row per bar —
    balance only changes when a trade closes (see `trade_simulator.py`'s
    "mark-to-close only" docstring), so one row per trade close (plus a
    leading point at the run's start) is already the complete, exact
    curve — nothing is downsampled or approximated.
    """

    __tablename__ = "equity_curve"
    __table_args__ = (Index("ix_equity_curve_run_time", "backtest_run_id", "time"),)

    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False, index=True)
    time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    drawdown_percent: Mapped[float] = mapped_column(Float, nullable=False)
    cumulative_pnl: Mapped[float] = mapped_column(Float, nullable=False)
    trade_count: Mapped[int] = mapped_column(Integer, nullable=False)
