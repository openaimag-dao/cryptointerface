from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import IdMixin, utcnow


class MarketStat(Base, IdMixin):
    """Latest 24h ticker snapshot for a symbol — one row per symbol, upserted
    on every REST/WS update so `/api/market` is a single indexed read."""

    __tablename__ = "market_stats"

    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    change_percent_24h: Mapped[float] = mapped_column(Float, nullable=False)
    high_24h: Mapped[float] = mapped_column(Float, nullable=False)
    low_24h: Mapped[float] = mapped_column(Float, nullable=False)
    volume_24h: Mapped[float] = mapped_column(Float, nullable=False)
    quote_volume_24h: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
