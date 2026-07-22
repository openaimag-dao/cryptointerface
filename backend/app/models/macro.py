from sqlalchemy import BigInteger, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class MacroDataPoint(Base, IdMixin, CreatedAtMixin):
    """One persisted macro-indicator reading (DXY, Gold, Fear & Greed, ...).

    Append-only history, one row per fetch — never upserted — so
    `/api/macro/indicators`'s "history" and any future charting can replay
    how an indicator moved over time. `indicator` is a stable slug (see
    `app/intelligence/macro/symbols.py`), `source` records which provider
    produced the value (useful once a symbol has more than one feed).
    """

    __tablename__ = "macro_data"
    __table_args__ = (Index("ix_macro_data_indicator_fetched_at", "indicator", "fetched_at"),)

    indicator: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    fetched_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
