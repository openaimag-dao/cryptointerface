from sqlalchemy import BigInteger, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class FundingRate(Base, IdMixin, CreatedAtMixin):
    """Funding rate snapshot for a perpetual futures symbol."""

    __tablename__ = "funding"
    __table_args__ = (
        UniqueConstraint("symbol", "funding_time", name="uq_funding_symbol_funding_time"),
        Index("ix_funding_symbol_funding_time", "symbol", "funding_time"),
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    funding_rate: Mapped[float] = mapped_column(Float, nullable=False)
    mark_price: Mapped[float] = mapped_column(Float, nullable=False)
    funding_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
