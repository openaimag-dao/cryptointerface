from sqlalchemy import JSON, BigInteger, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class SentimentScore(Base, IdMixin, CreatedAtMixin):
    """One persisted Sentiment Engine run: an overall read plus one row's
    worth of category breakdown, stored as JSON (see
    `app/intelligence/sentiment/engine.py`'s `SentimentResult`).

    Append-only history, same pattern as `ai_analysis` — every
    `/api/sentiment` call (or scheduled recompute) computes a fresh,
    deterministic-given-its-inputs blend and saves it here.
    """

    __tablename__ = "sentiment_scores"
    __table_args__ = (Index("ix_sentiment_scores_symbol_time", "symbol", "time"),)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    # {"technical": {"score":.., "confidence":.., "reasons": [...]}, "macro": {...}, ...}
    breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    reasons: Mapped[list] = mapped_column(JSON, nullable=False)
