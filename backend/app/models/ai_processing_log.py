from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class AIProcessingLog(Base, IdMixin, CreatedAtMixin):
    """One AI processing attempt for one article — summary generation,
    entity extraction, or importance scoring (see app/intelligence/llm/
    news_processing.py, Q4). Mirrors the fail-open philosophy used
    elsewhere: a SKIPPED/ERROR row means the article kept its
    deterministic fallback, not that ingestion failed."""

    __tablename__ = "ai_processing_logs"

    article_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)  # summary | entities | importance
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # SUCCESS | ERROR | SKIPPED
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
