from sqlalchemy import JSON, BigInteger, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class IndicatorValue(Base, IdMixin, CreatedAtMixin):
    """Computed indicator snapshot for one symbol/interval/candle.

    `payload` is a flexible JSON blob (see
    `app.services.indicators.engine.IndicatorSnapshot`) so adding a new
    indicator never requires a migration — just extend the engine and the
    Pydantic schema that serializes this column.

    Note: deliberately not named `values` — that collides with
    SQLAlchemy's `Insert.excluded.values` accessor (a method on the
    pseudo-table proxy) and silently upserts an empty JSON object instead
    of raising, so keep this named something else.
    """

    __tablename__ = "indicator_values"
    __table_args__ = (
        UniqueConstraint("symbol", "interval", "time", name="uq_indicator_values_symbol_interval_time"),
        Index("ix_indicator_values_symbol_interval_time", "symbol", "interval", "time"),
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
