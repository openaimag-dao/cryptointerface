from datetime import UTC, datetime

import pytest

from app.services.news_repository import get_articles_by_editorial_status, get_editorial_status_counts, insert_article


async def _insert(db_session, *, url: str, editorial_status: str = "PUBLISHED"):
    return await insert_article(
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


@pytest.mark.asyncio
async def test_get_articles_by_editorial_status_filters_correctly(db_session):
    await _insert(db_session, url="https://example.com/a", editorial_status="PENDING_REVIEW")
    await _insert(db_session, url="https://example.com/b", editorial_status="PUBLISHED")

    articles, total = await get_articles_by_editorial_status(db_session, "PENDING_REVIEW")

    assert total == 1
    assert articles[0].editorial_status == "PENDING_REVIEW"


@pytest.mark.asyncio
async def test_get_articles_by_editorial_status_paginates(db_session):
    for i in range(3):
        await _insert(db_session, url=f"https://example.com/{i}", editorial_status="PENDING_REVIEW")

    page1, total = await get_articles_by_editorial_status(db_session, "PENDING_REVIEW", limit=2, offset=0)
    page2, _ = await get_articles_by_editorial_status(db_session, "PENDING_REVIEW", limit=2, offset=2)

    assert total == 3
    assert len(page1) == 2
    assert len(page2) == 1


@pytest.mark.asyncio
async def test_get_editorial_status_counts_tallies_each_status(db_session):
    await _insert(db_session, url="https://example.com/a", editorial_status="PENDING_REVIEW")
    await _insert(db_session, url="https://example.com/b", editorial_status="PENDING_REVIEW")
    await _insert(db_session, url="https://example.com/c", editorial_status="PUBLISHED")

    counts = await get_editorial_status_counts(db_session)

    assert counts["PENDING_REVIEW"] == 2
    assert counts["PUBLISHED"] == 1


@pytest.mark.asyncio
async def test_get_editorial_status_counts_omits_statuses_with_no_articles(db_session):
    counts = await get_editorial_status_counts(db_session)
    assert counts == {}
