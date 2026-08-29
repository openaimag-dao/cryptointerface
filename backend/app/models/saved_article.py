from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class SavedArticle(Base, IdMixin, CreatedAtMixin):
    """A user's bookmark on a public article (Q2)."""

    __tablename__ = "saved_articles"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_saved_article_user_article"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False, index=True)
