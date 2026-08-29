from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class WatchlistItem(Base, IdMixin, CreatedAtMixin):
    """A user's private-dashboard watchlist entry (Q2). Architecture-only
    for now, per spec — no live price data is wired to this yet; that's
    future Market Data / Intelligence platform work, not this phase's."""

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
