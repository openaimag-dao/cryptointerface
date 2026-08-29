from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class NewsFetchLog(Base, IdMixin, CreatedAtMixin):
    """One RSS poll attempt for one source — powers the admin ingestion
    monitoring view (per-source health, error visibility, throughput)."""

    __tablename__ = "news_fetch_logs"

    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # SUCCESS | ERROR
    articles_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
