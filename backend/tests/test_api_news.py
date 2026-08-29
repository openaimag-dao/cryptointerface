"""Router-level (HTTP) tests for app/api/news.py's portal-facing endpoints
— /portal (pagination) and /{article_id} (detail), the two added for the
public news portal. The pre-existing list/latest/search endpoints already
have indirect coverage via test_news_repository.py's service-level tests;
these focus on what's new: status codes, topic validation, 404s, and the
route-ordering hazard between literal paths and the {article_id}: int
catch-all.
"""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.news import router as news_router
from app.database.session import get_db
from app.intelligence.llm.news_digest import NewsDigestResult
from app.services.news_digest_repository import insert_news_digest
from app.services.news_repository import insert_article


def _app(db_session):
    app = FastAPI()
    app.include_router(news_router)

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    return app


async def _client(db_session):
    transport = ASGITransport(app=_app(db_session))
    return AsyncClient(transport=transport, base_url="http://test")


async def _insert(db_session, *, url: str, title: str = "Title", portal_topic=None):
    return await insert_article(
        db_session,
        source="Test Source",
        title=title,
        summary="Summary text",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
        portal_topic=portal_topic,
    )


@pytest.mark.asyncio
async def test_portal_endpoint_returns_paginated_page(db_session):
    for i in range(3):
        await _insert(db_session, url=f"https://example.com/ai-{i}", portal_topic="AI")

    async with await _client(db_session) as client:
        response = await client.get("/api/news/portal", params={"topic": "AI", "limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["portalTopic"] == "AI"


@pytest.mark.asyncio
async def test_portal_endpoint_rejects_unknown_topic(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/news/portal", params={"topic": "SPORTS"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_portal_endpoint_without_topic_returns_everything(db_session):
    await _insert(db_session, url="https://example.com/a", portal_topic="AI")
    await _insert(db_session, url="https://example.com/b", portal_topic="CRYPTO")

    async with await _client(db_session) as client:
        response = await client.get("/api/news/portal")

    assert response.status_code == 200
    assert response.json()["total"] == 2


@pytest.mark.asyncio
async def test_get_article_by_id_200(db_session):
    await _insert(db_session, url="https://example.com/findme", title="Find Me")

    async with await _client(db_session) as client:
        page = await client.get("/api/news/portal", params={"limit": 1})
        article_id = page.json()["items"][0]["id"]
        response = await client.get(f"/api/news/{article_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Find Me"


@pytest.mark.asyncio
async def test_get_article_by_id_404_for_missing_article(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/news/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_literal_routes_are_not_shadowed_by_the_id_catch_all(db_session):
    """/latest, /search, /portal, and /digest must resolve to their own
    handlers, not fall into get_article(article_id: int) and 422 on type
    coercion — this only holds if the dynamic route is registered last."""
    async with await _client(db_session) as client:
        latest = await client.get("/api/news/latest")
        search = await client.get("/api/news/search", params={"q": "bitcoin"})
        portal = await client.get("/api/news/portal")
        digest = await client.get("/api/news/digest", params={"topic": "AI"})

    assert latest.status_code == 200
    assert search.status_code == 200
    assert portal.status_code == 200
    assert digest.status_code == 404  # no digest generated yet — still a real 404, not a 422


@pytest.mark.asyncio
async def test_digest_endpoint_rejects_unknown_topic(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/news/digest", params={"topic": "SPORTS"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_digest_endpoint_404_when_none_generated_yet(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/news/digest", params={"topic": "AI"})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_digest_endpoint_returns_the_latest_stored_digest(db_session):
    await insert_news_digest(
        db_session,
        NewsDigestResult(topic="AI", summary="AI is moving fast.", highlights=["A", "B"], article_count=3),
    )

    async with await _client(db_session) as client:
        response = await client.get("/api/news/digest", params={"topic": "AI"})

    assert response.status_code == 200
    body = response.json()
    assert body["topic"] == "AI"
    assert body["summary"] == "AI is moving fast."
    assert body["highlights"] == ["A", "B"]
    assert body["articleCount"] == 3
    assert body["generatedAt"]
