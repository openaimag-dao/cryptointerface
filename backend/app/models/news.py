from sqlalchemy import JSON, BigInteger, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class NewsArticle(Base, IdMixin, CreatedAtMixin):
    """One ingested news article (see app/intelligence/news/).

    `url` is unique — RSS feeds re-serve the same articles on every poll,
    so `news_repository.insert_article()` upserts on it (ON CONFLICT DO
    NOTHING) rather than accumulating duplicates. `symbols`/`impact_score`/
    `sentiment`/`category` are all computed once at ingest time by the
    deterministic classifier (`app/intelligence/news/classifier.py`) — no
    LLM call per article, see that module's docstring for why.

    `portal_topic` (CRYPTO/AI/BLOCKCHAIN/INNOVATION) is a separate,
    editorial taxonomy for the public news portal (Sprint 7) — deliberately
    not the same field as `category` (Security/Regulation/Institutional/
    DeFi/Technology/Market), which is a market-structure classification the
    trading terminal's news tab uses and which nothing else reads. Nullable
    because it's assigned by `classify_portal_topic()` at ingest; rows never
    get backfilled with a guess.
    """

    __tablename__ = "news"
    __table_args__ = (
        UniqueConstraint("url", name="uq_news_url"),
        Index("ix_news_published_at", "published_at"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    published_at: Mapped[int] = mapped_column(BigInteger, nullable=False)  # unix seconds
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    symbols: Mapped[list] = mapped_column(JSON, nullable=False)  # base asset tickers, e.g. ["BTC", "ETH"]
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(8), nullable=False)  # BULLISH | BEARISH | NEUTRAL
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    portal_topic: Mapped[str | None] = mapped_column(String(16), nullable=True)  # CRYPTO|AI|BLOCKCHAIN|INNOVATION
