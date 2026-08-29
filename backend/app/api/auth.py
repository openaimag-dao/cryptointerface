"""Real user accounts — register/login for the private dashboard. Reading
the public News Portal never requires one (see backend/README.md).

The frontend and backend are deployed on separate domains (Vercel /
Railway), so a cookie set here wouldn't be usable cross-origin — this API
returns the access token in the JSON body, and the frontend's own
`/api/auth/*` Route Handlers (Q2 frontend half) proxy through here and
set a first-party httpOnly cookie on their own domain.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.auth_service import (
    AuthNotConfiguredError,
    create_access_token,
    hash_password,
    verify_password,
)
from app.services.user_repository import create_user, get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"


def _to_user_out(user: User) -> UserOut:
    return UserOut(id=str(user.id), email=user.email, display_name=user.display_name, role=user.role)


def _issue_token(user: User) -> AuthResponse:
    try:
        token = create_access_token(user.id, user.role)
    except AuthNotConfiguredError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return AuthResponse(access_token=token, user=_to_user_out(user))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    # New accounts are always role="user" — there is no client-supplied
    # way to self-register as admin (see api/deps.py::get_current_admin_user).
    user = await create_user(
        db,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
    )
    return _issue_token(user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    user = await get_user_by_email(db, payload.email)
    # Same generic message whether the email is unknown or the password is
    # wrong — distinguishing the two lets an attacker enumerate accounts.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE)
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS_MESSAGE)

    return _issue_token(user)


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)) -> UserOut:
    return _to_user_out(user)
