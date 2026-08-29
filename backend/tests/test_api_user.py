from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.database.session import get_db
from app.models.news import NewsArticle
from app.services.news_repository import insert_article


def _app(db_session):
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(user_router)

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    return app


async def _client(db_session):
    transport = ASGITransport(app=_app(db_session))
    return AsyncClient(transport=transport, base_url="http://test")


async def _register_and_get_token(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/auth/register", json={"email": email, "password": "password123"})
    return response.json()["accessToken"]


async def _insert_article(db_session, url: str, title: str = "Title") -> int:
    await insert_article(
        db_session,
        source="Test Source",
        title=title,
        summary="Summary",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
    )
    result = await db_session.execute(select(NewsArticle).where(NewsArticle.url == url))
    return result.scalars().one().id


@pytest.mark.asyncio
async def test_bookmarks_endpoints_require_auth(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/user/bookmarks")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bookmark_add_list_and_remove_round_trip(db_session):
    article_id = await _insert_article(db_session, "https://example.com/bookmark-1")

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "bookmarker@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        add = await client.post(f"/api/user/bookmarks/{article_id}", headers=headers)
        listed = await client.get("/api/user/bookmarks", headers=headers)
        remove = await client.delete(f"/api/user/bookmarks/{article_id}", headers=headers)
        listed_after_remove = await client.get("/api/user/bookmarks", headers=headers)

    assert add.status_code == 204
    assert len(listed.json()["items"]) == 1
    assert listed.json()["items"][0]["id"] == str(article_id)
    assert remove.status_code == 204
    assert listed_after_remove.json()["items"] == []


@pytest.mark.asyncio
async def test_bookmark_unknown_article_returns_404(db_session):
    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "bookmarker2@example.com")
        response = await client.post(
            "/api/user/bookmarks/999999", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bookmarks_are_isolated_per_user(db_session):
    article_id = await _insert_article(db_session, "https://example.com/bookmark-2")

    async with await _client(db_session) as client:
        token_a = await _register_and_get_token(client, "usera@example.com")
        token_b = await _register_and_get_token(client, "userb@example.com")

        await client.post(f"/api/user/bookmarks/{article_id}", headers={"Authorization": f"Bearer {token_a}"})
        listed_b = await client.get("/api/user/bookmarks", headers={"Authorization": f"Bearer {token_b}"})

    assert listed_b.json()["items"] == []


@pytest.mark.asyncio
async def test_watchlist_endpoints_require_auth(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/user/watchlist")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_watchlist_add_and_remove_round_trip(db_session):
    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "watcher@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        add = await client.post("/api/user/watchlist", json={"symbol": "btc"}, headers=headers)
        remove = await client.delete("/api/user/watchlist/BTC", headers=headers)

    assert add.status_code == 201
    assert add.json()["symbols"] == ["BTC"]
    assert remove.status_code == 200
    assert remove.json()["symbols"] == []


@pytest.mark.asyncio
async def test_watchlist_is_isolated_per_user(db_session):
    async with await _client(db_session) as client:
        token_a = await _register_and_get_token(client, "watchera@example.com")
        token_b = await _register_and_get_token(client, "watcherb@example.com")

        await client.post("/api/user/watchlist", json={"symbol": "BTC"}, headers={"Authorization": f"Bearer {token_a}"})
        listed_b = await client.get("/api/user/watchlist", headers={"Authorization": f"Bearer {token_b}"})

    assert listed_b.json()["symbols"] == []
