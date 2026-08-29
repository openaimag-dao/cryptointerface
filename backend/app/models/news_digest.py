from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class NewsDigest(Base, IdMixin, CreatedAtMixin):
    """One AI-narrated digest of a portal topic's recent real headlines.

    Generated periodically by `run_news_digest_refresh` (see
    app/intelligence/scheduler/tasks.py) from `app/intelligence/llm/
    news_digest.py`, not on-demand per request — same reasoning as
    `LlmReport`/the Dashboard Intelligence Card: a public portal page must
    stay cheap to serve, so the Claude call happens on a schedule and the
    API only ever reads the latest stored row. `created_at` (from
    CreatedAtMixin) doubles as "generated at".
    """

    __tablename__ = "news_digests"

    topic: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    highlights: Mapped[list] = mapped_column(JSON, nullable=False)
    article_count: Mapped[int] = mapped_column(Integer, nullable=False)
