from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class Symbol(Base, IdMixin, CreatedAtMixin):
    """A tradable instrument tracked by the Data Engine (e.g. BTCUSDT)."""

    __tablename__ = "symbols"

    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    base_asset: Mapped[str] = mapped_column(String(16), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(16), nullable=False)
    price_precision: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    quantity_precision: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
