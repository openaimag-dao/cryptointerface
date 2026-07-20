from sqlalchemy import BigInteger, Boolean, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class Candle(Base, IdMixin, CreatedAtMixin):
    """OHLCV candle for one symbol/interval/open_time.

    `open_time` is stored as a unix-seconds integer (matches Binance kline
    `t` field / TradingView Lightweight Charts `time`), not a DateTime, so
    it round-trips to the frontend without timezone conversion.
    """

    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("symbol", "interval", "open_time", name="uq_candles_symbol_interval_open_time"),
        Index("ix_candles_symbol_interval_open_time", "symbol", "interval", "open_time"),
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    open_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    close_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    quote_volume: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trades: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
