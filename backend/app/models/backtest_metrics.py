from sqlalchemy import BigInteger, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class BacktestMetrics(Base, IdMixin, CreatedAtMixin):
    """The full performance + risk metric set for one backtest run — one
    row per run (`backtest_run_id` unique). See `app/backtesting/performance.py`
    and `app/backtesting/risk_metrics.py` for how each field is computed,
    and `backend/README.md`'s Backtesting Engine section for the formulas.
    """

    __tablename__ = "backtest_metrics"

    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False, unique=True)

    total_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, nullable=False)

    total_return_percent: Mapped[float] = mapped_column(Float, nullable=False)
    net_profit: Mapped[float] = mapped_column(Float, nullable=False)
    gross_profit: Mapped[float] = mapped_column(Float, nullable=False)
    gross_loss: Mapped[float] = mapped_column(Float, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False)
    loss_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_win: Mapped[float] = mapped_column(Float, nullable=False)
    avg_loss: Mapped[float] = mapped_column(Float, nullable=False)
    profit_factor: Mapped[float] = mapped_column(Float, nullable=False)
    expectancy: Mapped[float] = mapped_column(Float, nullable=False)
    avg_trade_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    max_drawdown_percent: Mapped[float] = mapped_column(Float, nullable=False)
    recovery_factor: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    sortino_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    calmar_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    avg_risk_reward: Mapped[float] = mapped_column(Float, nullable=False)

    final_balance: Mapped[float] = mapped_column(Float, nullable=False)
    peak_balance: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown_duration_seconds: Mapped[int] = mapped_column(BigInteger, nullable=False)
