"""Password hashing + JWT issuance/verification for real user accounts.

Separate from every other AI-powered service in this codebase — this is
plain, deterministic security-critical code with zero LLM involvement.
Fails closed (unlike this codebase's usual data-enrichment fail-open
pattern) when `JWT_SECRET_KEY` isn't configured: an unconfigured secret
means tokens can't be safely verified, so register/login must refuse
rather than issue something insecure.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

NOT_CONFIGURED_MESSAGE = (
    "Authentication isn't configured yet — set JWT_SECRET_KEY in backend/.env and restart the backend."
)


class AuthNotConfiguredError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    role: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise AuthNotConfiguredError(NOT_CONFIGURED_MESSAGE)

    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise AuthNotConfiguredError(NOT_CONFIGURED_MESSAGE)

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    try:
        return TokenPayload(user_id=int(payload["sub"]), role=payload["role"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("Malformed token payload") from exc
