from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.database.session import get_db
from app.models.news_source import NewsSource
from app.models.user import User
from app.services.news_repository import insert_article
from app.services.news_source_repository import record_fetch_result


def _app(db_session):
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(admin_router)

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


async def _promote_to_admin(db_session, email: str) -> None:
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().one()
    user.role = "admin"
    await db_session.commit()


async def _insert_article(db_session, *, url: str, editorial_status: str = "PENDING_REVIEW") -> int:
    from app.models.news import NewsArticle

    await insert_article(
        db_session,
        source="Test Source",
        title="Title",
        summary="Summary",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
        editorial_status=editorial_status,
    )
    result = await db_session.execute(select(NewsArticle).where(NewsArticle.url == url))
    return result.scalars().one().id


@pytest.mark.asyncio
async def test_admin_news_requires_auth(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/admin/news")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_news_rejects_a_non_admin_user(db_session):
    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "regular@example.com")
        response = await client.get("/api/admin/news", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_news_returns_pending_review_by_default(db_session):
    await _insert_article(db_session, url="https://example.com/pending", editorial_status="PENDING_REVIEW")
    await _insert_article(db_session, url="https://example.com/published", editorial_status="PUBLISHED")

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin@example.com")
        await _promote_to_admin(db_session, "admin@example.com")
        response = await client.get("/api/admin/news", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://example.com/pending"


@pytest.mark.asyncio
async def test_admin_news_rejects_unknown_status_filter(db_session):
    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin2@example.com")
        await _promote_to_admin(db_session, "admin2@example.com")
        response = await client.get(
            "/api/admin/news", params={"status": "NOT_A_REAL_STATUS"}, headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_news_counts_tallies_by_status(db_session):
    await _insert_article(db_session, url="https://example.com/a", editorial_status="PENDING_REVIEW")
    await _insert_article(db_session, url="https://example.com/b", editorial_status="PUBLISHED")

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin3@example.com")
        await _promote_to_admin(db_session, "admin3@example.com")
        response = await client.get("/api/admin/news/counts", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    counts = response.json()["counts"]
    assert counts["PENDING_REVIEW"] == 1
    assert counts["PUBLISHED"] == 1
    assert counts["REJECTED"] == 0


@pytest.mark.asyncio
async def test_admin_can_approve_a_pending_article(db_session):
    article_id = await _insert_article(db_session, url="https://example.com/approve")

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin4@example.com")
        await _promote_to_admin(db_session, "admin4@example.com")
        response = await client.patch(
            f"/api/admin/news/{article_id}",
            json={"editorialStatus": "PUBLISHED"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["id"] == str(article_id)

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin5@example.com")
        await _promote_to_admin(db_session, "admin5@example.com")
        published = await client.get(
            "/api/admin/news", params={"status": "PUBLISHED"}, headers={"Authorization": f"Bearer {token}"}
        )
    assert published.json()["total"] == 1


@pytest.mark.asyncio
async def test_admin_can_edit_article_fields(db_session):
    article_id = await _insert_article(db_session, url="https://example.com/edit")

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin6@example.com")
        await _promote_to_admin(db_session, "admin6@example.com")
        response = await client.patch(
            f"/api/admin/news/{article_id}",
            json={"title": "Edited Title", "summary": "Edited summary."},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Edited Title"
    assert response.json()["summary"] == "Edited summary."


@pytest.mark.asyncio
async def test_admin_update_rejects_unknown_status(db_session):
    article_id = await _insert_article(db_session, url="https://example.com/badstatus")

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin7@example.com")
        await _promote_to_admin(db_session, "admin7@example.com")
        response = await client.patch(
            f"/api/admin/news/{article_id}",
            json={"editorialStatus": "NOT_A_REAL_STATUS"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_update_404_for_unknown_article(db_session):
    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin8@example.com")
        await _promote_to_admin(db_session, "admin8@example.com")
        response = await client.patch(
            "/api/admin/news/999999", json={"title": "x"}, headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_sources_requires_auth(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/admin/sources")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_list_sources(db_session):
    source = NewsSource(source_key="src-a", name="Source A", rss_url="https://example.com/a")
    db_session.add(source)
    await db_session.commit()

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin9@example.com")
        await _promote_to_admin(db_session, "admin9@example.com")
        response = await client.get("/api/admin/sources", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["sourceKey"] == "src-a"
    assert body[0]["enabled"] is True


@pytest.mark.asyncio
async def test_admin_can_toggle_a_source(db_session):
    source = NewsSource(source_key="src-b", name="Source B", rss_url="https://example.com/b")
    db_session.add(source)
    await db_session.commit()
    source_id = source.id

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin10@example.com")
        await _promote_to_admin(db_session, "admin10@example.com")
        response = await client.patch(
            f"/api/admin/sources/{source_id}",
            json={"enabled": False, "autoPublish": False},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["autoPublish"] is False


@pytest.mark.asyncio
async def test_admin_update_source_404_for_unknown_source(db_session):
    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin11@example.com")
        await _promote_to_admin(db_session, "admin11@example.com")
        response = await client.patch(
            "/api/admin/sources/999999", json={"enabled": False}, headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_list_fetch_logs(db_session):
    source = NewsSource(source_key="src-c", name="Source C", rss_url="https://example.com/c")
    db_session.add(source)
    await db_session.commit()
    await record_fetch_result(db_session, source, status="ERROR", articles_found=0, articles_new=0, duration_ms=5)

    async with await _client(db_session) as client:
        token = await _register_and_get_token(client, "admin12@example.com")
        await _promote_to_admin(db_session, "admin12@example.com")
        response = await client.get("/api/admin/fetch-logs", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["sourceName"] == "Source C"
    assert body[0]["status"] == "ERROR"
