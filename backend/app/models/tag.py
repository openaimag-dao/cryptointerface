from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class Tag(Base, IdMixin, CreatedAtMixin):
    """A free-form topical label attached to articles via `ArticleTag`
    (many-to-many) — distinct from `NewsArticle.portal_topic` (one of 4
    fixed values) and `Entity` (a named thing the AI extracted)."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
