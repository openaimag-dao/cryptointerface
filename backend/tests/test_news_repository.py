from datetime import UTC, datetime

import pytest

from app.services.news_repository import (
    get_article_by_id,
    get_latest_news,
    get_news_snapshot_for_symbol,
    get_portal_news_page,
    insert_article,
    search_news,
)


async def _insert(
    db_session,
    *,
    url: str,
    title: str = "Title",
    symbols=None,
    sentiment="NEUTRAL",
    impact=50.0,
    portal_topic=None,
):
    return await insert_article(
        db_session,
        source="Test Source",
        title=title,
        summary="Summary text",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=symbols or [],
        impact_score=impact,
        sentiment=sentiment,
        category="Market",
        portal_topic=portal_topic,
    )


@pytest.mark.asyncio
async def test_insert_article_dedupes_on_url(db_session):
    first = await _insert(db_session, url="https://example.com/a")
    second = await _insert(db_session, url="https://example.com/a")

    assert first is True
    assert second is False

    articles = await get_latest_news(db_session, limit=10)
    assert len(articles) == 1


@pytest.mark.asyncio
async def test_get_latest_news_filters_by_symbol(db_session):
    await _insert(db_session, url="https://example.com/btc", symbols=["BTC"])
    await _insert(db_session, url="https://example.com/eth", symbols=["ETH"])

    btc_only = await get_latest_news(db_session, limit=10, symbol="BTC")

    assert len(btc_only) == 1
    assert btc_only[0].symbols == ["BTC"]


@pytest.mark.asyncio
async def test_search_news_matches_title_or_summary(db_session):
    await _insert(db_session, url="https://example.com/a", title="Bitcoin rallies hard")
    await _insert(db_session, url="https://example.com/b", title="Unrelated headline")

    results = await search_news(db_session, "bitcoin")

    assert len(results) == 1
    assert "Bitcoin" in results[0].title


@pytest.mark.asyncio
async def test_get_news_snapshot_for_symbol_none_without_relevant_news(db_session):
    snapshot = await get_news_snapshot_for_symbol(db_session, "BTC")
    assert snapshot is None


@pytest.mark.asyncio
async def test_get_news_snapshot_for_symbol_weights_by_impact(db_session):
    await _insert(db_session, url="https://example.com/bull", symbols=["BTC"], sentiment="BULLISH", impact=90.0)
    await _insert(db_session, url="https://example.com/bear", symbols=["BTC"], sentiment="BEARISH", impact=10.0)

    snapshot = await get_news_snapshot_for_symbol(db_session, "BTC")

    assert snapshot is not None
    assert snapshot.article_count == 2
    # High-impact bullish article should dominate the low-impact bearish one.
    assert snapshot.avg_sentiment_score > 50.0


@pytest.mark.asyncio
async def test_get_news_snapshot_includes_untagged_market_wide_articles(db_session):
    await _insert(db_session, url="https://example.com/market", symbols=[], sentiment="BEARISH", impact=80.0)

    snapshot = await get_news_snapshot_for_symbol(db_session, "BTC")

    assert snapshot is not None
    assert snapshot.article_count == 1


@pytest.mark.asyncio
async def test_get_latest_news_filters_by_portal_topic(db_session):
    await _insert(db_session, url="https://example.com/ai", portal_topic="AI")
    await _insert(db_session, url="https://example.com/crypto", portal_topic="CRYPTO")

    ai_only = await get_latest_news(db_session, limit=10, topic="AI")

    assert len(ai_only) == 1
    assert ai_only[0].portal_topic == "AI"


@pytest.mark.asyncio
async def test_get_portal_news_page_paginates_and_counts_by_topic(db_session):
    for i in range(5):
        await _insert(db_session, url=f"https://example.com/ai-{i}", portal_topic="AI")
    await _insert(db_session, url="https://example.com/crypto-only", portal_topic="CRYPTO")

    page1, total = await get_portal_news_page(db_session, topic="AI", limit=2, offset=0)
    page2, total2 = await get_portal_news_page(db_session, topic="AI", limit=2, offset=2)

    assert total == total2 == 5
    assert len(page1) == 2
    assert len(page2) == 2
    assert {a.url for a in page1}.isdisjoint({a.url for a in page2})


@pytest.mark.asyncio
async def test_get_portal_news_page_without_topic_returns_everything(db_session):
    await _insert(db_session, url="https://example.com/a", portal_topic="AI")
    await _insert(db_session, url="https://example.com/b", portal_topic="CRYPTO")

    articles, total = await get_portal_news_page(db_session, topic=None, limit=10, offset=0)

    assert total == 2
    assert len(articles) == 2


@pytest.mark.asyncio
async def test_get_article_by_id_returns_none_for_missing_article(db_session):
    article = await get_article_by_id(db_session, 999999)
    assert article is None


@pytest.mark.asyncio
async def test_get_article_by_id_returns_the_inserted_article(db_session):
    await _insert(db_session, url="https://example.com/findme", title="Find Me")

    articles, _ = await get_portal_news_page(db_session, limit=1)
    found = await get_article_by_id(db_session, articles[0].id)

    assert found is not None
    assert found.title == "Find Me"
