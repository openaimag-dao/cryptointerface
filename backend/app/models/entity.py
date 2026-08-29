from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin

ENTITY_TYPES = ("COMPANY", "PERSON", "CRYPTOCURRENCY", "PROTOCOL", "COUNTRY", "TECHNOLOGY")


class Entity(Base, IdMixin, CreatedAtMixin):
    """A named thing (company, person, cryptocurrency, protocol, country,
    or technology) the AI Processing layer (app/intelligence/llm/
    entity_extraction.py, Q4) found mentioned in an article. Linked via
    `ArticleEntity` (many-to-many) — one entity can span many articles,
    which is what lets `NewsEvent` grouping and Trending work off it."""

    __tablename__ = "entities"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    entity_type: Mapped[str] = mapped_column(String(16), nullable=False)
