from sqlalchemy import JSON, BigInteger, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class AIAnalysis(Base, IdMixin, CreatedAtMixin):
    """One persisted AI Decision Engine run.

    Append-only history (no upsert/unique constraint on purpose) — every
    `/api/ai/*` call computes a fresh, deterministic analysis and saves it
    here, so results are auditable and comparable over time.

    `factors`/`reasons` (Sprint 6) capture the same per-factor scores and
    human-readable reasons the API response already returns for a live
    call — persisted so the Confidence Timeline can diff two real,
    historical decisions instead of re-deriving them. Nullable because
    rows written before this column existed have neither; the timeline
    reports that honestly instead of backfilling a guess.
    """

    __tablename__ = "ai_analysis"
    __table_args__ = (Index("ix_ai_analysis_symbol_interval_time", "symbol", "interval", "time"),)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp1: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp2: Mapped[float | None] = mapped_column(Float, nullable=True)
    tp3: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    factors: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)  # {factor_name: score}
    reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
