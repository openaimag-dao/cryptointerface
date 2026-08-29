import time

import jwt
import pytest

from app.core.config import get_settings
from app.services.auth_service import (
    AuthNotConfiguredError,
    InvalidTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_a_verifiable_hash():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)


def test_verify_password_rejects_the_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("wrong password", hashed) is False


def test_create_and_decode_access_token_round_trips():
    token = create_access_token(user_id=42, role="user")
    payload = decode_access_token(token)
    assert payload.user_id == 42
    assert payload.role == "user"


def test_decode_access_token_rejects_a_tampered_token():
    token = create_access_token(user_id=42, role="user")
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_decode_access_token_rejects_an_expired_token(monkeypatch):
    settings = get_settings()
    # Sign a token that's already expired, using the real secret so only
    # expiry (not signature) is under test.
    expired_payload = {"sub": "1", "role": "user", "iat": int(time.time()) - 120, "exp": int(time.time()) - 60}
    expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(InvalidTokenError):
        decode_access_token(expired_token)


def test_create_access_token_fails_closed_without_a_configured_secret(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_secret_key", "")

    with pytest.raises(AuthNotConfiguredError):
        create_access_token(user_id=1, role="user")


def test_decode_access_token_fails_closed_without_a_configured_secret(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_secret_key", "")

    with pytest.raises(AuthNotConfiguredError):
        decode_access_token("anything")
