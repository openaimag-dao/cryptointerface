from sqlalchemy import BigInteger, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class OpenInterest(Base, IdMixin, CreatedAtMixin):
    """Open interest snapshot for a perpetual futures symbol."""

    __tablename__ = "open_interest"
    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", name="uq_open_interest_symbol_timestamp"),
        Index("ix_open_interest_symbol_timestamp", "symbol", "timestamp"),
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    open_interest: Mapped[float] = mapped_column(Float, nullable=False)
    open_interest_value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
