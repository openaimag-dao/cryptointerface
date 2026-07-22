from sqlalchemy import BigInteger, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class WhaleEvent(Base, IdMixin, CreatedAtMixin):
    """One large on-chain transfer touching a known exchange wallet (see
    app/intelligence/whales/). Append-only, deduped on `tx_hash` — the
    same on-chain transaction is never persisted twice even if a poll
    cycle re-fetches it.
    """

    __tablename__ = "whale_events"
    __table_args__ = (
        UniqueConstraint("tx_hash", name="uq_whale_events_tx_hash"),
        Index("ix_whale_events_asset_timestamp", "asset", "timestamp"),
    )

    asset: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    usd_value: Mapped[float] = mapped_column(Float, nullable=False)
    wallet_type: Mapped[str] = mapped_column(String(16), nullable=False)  # EXCHANGE | UNKNOWN
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # TO_EXCHANGE | FROM_EXCHANGE
    exchange: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    from_address: Mapped[str] = mapped_column(String(64), nullable=False)
    to_address: Mapped[str] = mapped_column(String(64), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(80), nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)  # unix seconds
