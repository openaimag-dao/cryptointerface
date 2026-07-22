from datetime import UTC, datetime

import pytest

from app.services.news_repository import (
    get_latest_news,
    get_news_snapshot_for_symbol,
    insert_article,
    search_news,
)


async def _insert(db_session, *, url: str, title: str = "Title", symbols=None, sentiment="NEUTRAL", impact=50.0):
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
