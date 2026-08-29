from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class NewsSource(Base, IdMixin, CreatedAtMixin):
    """Admin-manageable RSS source — the DB-backed counterpart to the seed
    definitions in app/intelligence/news/sources.py (`NEWS_SOURCES`).

    Those static definitions only ever populate this table once, via
    `seed_default_sources()` on startup (idempotent upsert on
    `source_key`). After that, this table is the ingestion pipeline's
    source of truth: `fetch_and_persist_news()` iterates enabled rows
    here, not the static list — so an admin disabling, editing, or
    retrusting a source takes effect on the next poll cycle with no
    deploy. `auto_publish=False` sends that source's new articles to
    `PENDING_REVIEW` instead of `PUBLISHED` (see NewsArticle.editorial_status).
    """

    __tablename__ = "news_sources"

    source_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rss_url: Mapped[str] = mapped_column(String(500), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    country: Mapped[str | None] = mapped_column(String(4), nullable=True)
    default_topic: Mapped[str] = mapped_column(String(16), nullable=False, default="CRYPTO")
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=70.0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auto_publish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(16), nullable=True)  # SUCCESS | ERROR
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    articles_imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def to_source_def(self):
        from app.intelligence.news.sources import NewsSourceDef

        return NewsSourceDef(
            id=self.source_key,
            name=self.name,
            rss_url=self.rss_url,
            language=self.language,
            default_topic=self.default_topic,
        )
