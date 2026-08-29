from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin

# Languages the translation pipeline (app/intelligence/llm/news_translation.py)
# produces. English is the ingested original — never a "translation" row.
SUPPORTED_TRANSLATION_LANGUAGES = ("ru", "kk")


class ArticleTranslation(Base, IdMixin, CreatedAtMixin):
    """A Claude-translated title + summary for one article, one target
    language. Deliberately a separate table keyed on `article_id`, not
    extra `title_ru`/`title_kk` columns on `NewsArticle` and not a
    duplicated `NewsArticle` row per language — the original spec calls
    this out explicitly ("multilingual-ready... without duplicating
    articles per language"). Adding a third language later is a data
    migration, not a schema change.

    Same anti-fabrication discipline as news_processing.py (Q4): Claude
    is given only the real ingested title/summary and instructed to
    translate faithfully, never add or omit information.
    """

    __tablename__ = "article_translations"
    __table_args__ = (UniqueConstraint("article_id", "language", name="uq_article_translation_article_language"),)

    article_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
