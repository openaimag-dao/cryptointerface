from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class Author(Base, IdMixin, CreatedAtMixin):
    """A byline. Real editorial staff (future) and the synthetic
    "AIMAG News Desk" attribution used for auto-published wire aggregation
    both live here, so every article always has a displayable author."""

    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
