from sqlalchemy import JSON, BigInteger, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class LlmReport(Base, IdMixin, CreatedAtMixin):
    """One persisted LLM explanation of an already-computed AI Decision.

    The LLM never sets `direction`/`confidence` itself — both are copied
    straight from `AIDecision` (see `app/ai_engine/decision_engine.py`) so
    the explanation can never disagree with the deterministic engine it is
    describing. Only `summary`/`key_drivers`/`risks`/`opportunities`/
    `assets_affected` are model output (see
    `app/intelligence/llm/explanation.py`).
    """

    __tablename__ = "llm_reports"
    __table_args__ = (Index("ix_llm_reports_symbol_time", "symbol", "time"),)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)
    key_drivers: Mapped[list] = mapped_column(JSON, nullable=False)
    risks: Mapped[list] = mapped_column(JSON, nullable=False)
    opportunities: Mapped[list] = mapped_column(JSON, nullable=False)
    assets_affected: Mapped[list] = mapped_column(JSON, nullable=False)
