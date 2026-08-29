import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.database.session import get_db


def _app(db_session):
    app = FastAPI()
    app.include_router(auth_router)

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    return app


async def _client(db_session):
    transport = ASGITransport(app=_app(db_session))
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_register_returns_a_token_and_the_new_user(db_session):
    async with await _client(db_session) as client:
        response = await client.post(
            "/api/auth/register", json={"email": "new@example.com", "password": "password123", "displayName": "New"}
        )

    assert response.status_code == 201
    body = response.json()
    assert body["accessToken"]
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["displayName"] == "New"
    assert body["user"]["role"] == "user"


@pytest.mark.asyncio
async def test_register_rejects_a_duplicate_email(db_session):
    async with await _client(db_session) as client:
        await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
        response = await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_rejects_a_short_password(db_session):
    async with await _client(db_session) as client:
        response = await client.post("/api/auth/register", json={"email": "short@example.com", "password": "short"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_succeeds_with_correct_credentials(db_session):
    async with await _client(db_session) as client:
        await client.post("/api/auth/register", json={"email": "login@example.com", "password": "password123"})
        response = await client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})

    assert response.status_code == 200
    assert response.json()["accessToken"]


@pytest.mark.asyncio
async def test_login_rejects_the_wrong_password(db_session):
    async with await _client(db_session) as client:
        await client.post("/api/auth/register", json={"email": "wrongpw@example.com", "password": "password123"})
        response = await client.post(
            "/api/auth/login", json={"email": "wrongpw@example.com", "password": "nope-nope-nope"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_an_unknown_email(db_session):
    async with await _client(db_session) as client:
        response = await client.post(
            "/api/auth/login", json={"email": "ghost@example.com", "password": "password123"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_the_current_user_with_a_valid_token(db_session):
    async with await _client(db_session) as client:
        register = await client.post(
            "/api/auth/register", json={"email": "me@example.com", "password": "password123"}
        )
        token = register.json()["accessToken"]
        response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_rejects_a_missing_token(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_rejects_a_garbage_token(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_fails_closed_without_a_configured_jwt_secret(db_session, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_secret_key", "")

    async with await _client(db_session) as client:
        response = await client.post(
            "/api/auth/register", json={"email": "noauth@example.com", "password": "password123"}
        )

    assert response.status_code == 503
