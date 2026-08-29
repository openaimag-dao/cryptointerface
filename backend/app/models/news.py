from sqlalchemy import JSON, BigInteger, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin

# imported: just written by the fetcher, not yet classified/AI-processed (transient in practice).
# processing: classifier/AI stages running.
# pending_review: source has auto_publish=False — waiting on an editor.
# approved: editor signed off, not yet live.
# published: live on the public portal (the only state that existed before Q1 — RSS
#   auto-publish sources default straight here, so existing behavior is unchanged).
# rejected / archived: editor pulled it, or it aged out.
EDITORIAL_STATUSES = ("IMPORTED", "PROCESSING", "PENDING_REVIEW", "APPROVED", "PUBLISHED", "REJECTED", "ARCHIVED")


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

    `slug`/`editorial_status`/`news_event_id`/`author_id`/`ai_summary` are
    the News Platform foundation (Q1): SEO-friendly URLs, the editorial
    workflow (Q5), deduplication grouping (Q3), and a byline + an
    AI-generated original summary distinct from the raw RSS `summary`
    (Q4) — respectively. All nullable/defaulted so every pre-existing row
    and every current News Engine consumer keeps working unchanged.
    """

    __tablename__ = "news"
    __table_args__ = (
        UniqueConstraint("url", name="uq_news_url"),
        UniqueConstraint("slug", name="uq_news_slug"),
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
    slug: Mapped[str | None] = mapped_column(String(140), nullable=True)
    editorial_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PUBLISHED")
    news_event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("authors.id"), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # A real image URL pulled straight from the RSS entry itself (Media RSS
    # or a plain enclosure — see intelligence/news/fetcher.py::
    # _entry_image_url), never fabricated. Null when the source's feed
    # genuinely doesn't include one — the frontend renders a text-only
    # card in that case rather than a placeholder graphic.
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
