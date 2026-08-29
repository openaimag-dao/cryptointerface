from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import CreatedAtMixin, IdMixin


class User(Base, IdMixin, CreatedAtMixin):
    """A registered account for the public site — reading news never
    requires one; this backs `/login`, `/register`, and the private
    dashboard (saved articles, watchlist) added in Q2. `role` gates the
    admin panel (Q5): "admin" vs "user", checked per-request, not implied
    by any client-supplied value."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")  # user | admin
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
