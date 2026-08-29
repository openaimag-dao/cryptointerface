import pytest

from app.intelligence.llm.news_digest import NewsDigestResult
from app.services.news_digest_repository import get_latest_news_digest, insert_news_digest


@pytest.mark.asyncio
async def test_get_latest_news_digest_returns_none_when_nothing_generated_yet(db_session):
    digest = await get_latest_news_digest(db_session, "AI")
    assert digest is None


@pytest.mark.asyncio
async def test_insert_and_get_latest_news_digest_round_trips(db_session):
    result = NewsDigestResult(
        topic="AI",
        summary="AI is moving fast.",
        highlights=["Thing one", "Thing two"],
        article_count=5,
    )

    await insert_news_digest(db_session, result)
    digest = await get_latest_news_digest(db_session, "AI")

    assert digest is not None
    assert digest.topic == "AI"
    assert digest.summary == "AI is moving fast."
    assert digest.highlights == ["Thing one", "Thing two"]
    assert digest.article_count == 5
    assert digest.created_at is not None


@pytest.mark.asyncio
async def test_get_latest_news_digest_filters_by_topic(db_session):
    await insert_news_digest(
        db_session, NewsDigestResult(topic="AI", summary="AI summary", highlights=[], article_count=1)
    )
    await insert_news_digest(
        db_session, NewsDigestResult(topic="CRYPTO", summary="Crypto summary", highlights=[], article_count=1)
    )

    digest = await get_latest_news_digest(db_session, "CRYPTO")

    assert digest is not None
    assert digest.summary == "Crypto summary"


@pytest.mark.asyncio
async def test_get_latest_news_digest_returns_the_most_recent(db_session):
    await insert_news_digest(
        db_session, NewsDigestResult(topic="AI", summary="Older", highlights=[], article_count=1)
    )
    await insert_news_digest(
        db_session, NewsDigestResult(topic="AI", summary="Newer", highlights=[], article_count=2)
    )

    digest = await get_latest_news_digest(db_session, "AI")

    assert digest is not None
    assert digest.summary == "Newer"
