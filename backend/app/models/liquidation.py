from sqlalchemy import BigInteger, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class LiquidationEvent(Base, IdMixin, CreatedAtMixin):
    """One forced-liquidation fill from Binance's `forceOrder` stream.

    Append-only (no upsert) — every liquidation is a distinct event, not
    something that gets revised, matching `AIAnalysis`'s history pattern.
    """

    __tablename__ = "liquidations"
    __table_args__ = (Index("ix_liquidations_symbol_timestamp", "symbol", "timestamp"),)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)  # "LONG" | "SHORT" — liquidated position's side
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False, default="Binance")
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)  # unix ms, Binance's order trade time
