"""FastAPI dependencies for authenticated routes (private dashboard, and
the future admin panel — see `get_current_admin_user`)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import AuthNotConfiguredError, InvalidTokenError, decode_access_token
from app.services.user_repository import get_user_by_id

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
    except AuthNotConfiguredError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from exc

    user = await get_user_by_id(db, payload.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """For the admin panel (Q5). Checked against the DB-persisted `role`
    on every request — never inferred from the token's claimed role alone
    beyond what decode_access_token already trusts, and never settable by
    the registering user (see api/auth.py: register always defaults to
    "user")."""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user
