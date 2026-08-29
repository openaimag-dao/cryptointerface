from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class NewsEvent(Base, IdMixin, CreatedAtMixin):
    """Groups multiple `NewsArticle` rows that cover the same real-world
    event across sources — see app/intelligence/news/dedup.py (Q3).
    `primary_article_id` is the canonical article (earliest/most
    authoritative source) used when rendering the event as one story with
    multiple sources listed, instead of N near-identical cards."""

    __tablename__ = "news_events"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    portal_topic: Mapped[str | None] = mapped_column(String(16), nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # use_alter breaks the news<->news_events circular FK (news.news_event_id
    # references this table too) so SQLAlchemy can order CREATE/DROP TABLE;
    # it emits this one as a separate ALTER TABLE ADD/DROP CONSTRAINT.
    primary_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news.id", use_alter=True, name="fk_news_events_primary_article_id"), nullable=True
    )
