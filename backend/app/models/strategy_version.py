from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class StrategyVersion(Base, IdMixin, CreatedAtMixin):
    """One named, versioned snapshot of the strategy a backtest run
    replays. Today there is exactly one real strategy — the unmodified
    Sprint 3 AI Decision Engine (`app/ai_engine/decision_engine.py`) — so
    `config` is a JSON audit snapshot of its tunable constants (confidence
    floor, Market Score factor weights, ATR/R-multiple settings) at the
    time this version was recorded, not a set of knobs that actually
    change engine behavior yet. It exists now so `backtest_runs` always
    references a concrete, reproducible version, and so Sprint 5's
    `optimizer.py` (interface-only for now, see its docstring) has
    somewhere to write a *new* row once real parameter tuning lands.
    """

    __tablename__ = "strategy_versions"

    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # {"min_confidence_for_action": 45.0, "factor_weights": {...}, "tp_r_multiples": [1.5, 2.5, 4.0], ...}
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
