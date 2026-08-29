from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.news import NewsArticle
from app.models.news_event import NewsEvent
from app.services.news_repository import (
    get_article_by_id,
    get_latest_news,
    get_news_snapshot_for_symbol,
    get_portal_news_page,
    get_trending_news,
    get_unprocessed_articles,
    insert_article,
    search_news,
)


async def _insert(
    db_session,
    *,
    url: str,
    title: str = "Title",
    summary: str = "Summary text",
    symbols=None,
    sentiment="NEUTRAL",
    impact=50.0,
    portal_topic=None,
    editorial_status="PUBLISHED",
    published_at: int | None = None,
):
    return await insert_article(
        db_session,
        source="Test Source",
        title=title,
        summary=summary,
        url=url,
        published_at=published_at if published_at is not None else int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=symbols or [],
        impact_score=impact,
        sentiment=sentiment,
        category="Market",
        portal_topic=portal_topic,
        editorial_status=editorial_status,
    )


async def _insert_and_fetch(db_session, **kwargs) -> NewsArticle:
    await _insert(db_session, **kwargs)
    result = await db_session.execute(select(NewsArticle).where(NewsArticle.url == kwargs["url"]))
    return result.scalars().one()


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

    results, total = await search_news(db_session, "bitcoin")

    assert total == 1
    assert len(results) == 1
    assert "Bitcoin" in results[0].title


@pytest.mark.asyncio
async def test_search_news_ranks_title_matches_above_summary_only_matches(db_session):
    await _insert(
        db_session,
        url="https://example.com/summary-only",
        title="Market roundup",
        summary="Ethereum had a quiet day overall.",
    )
    await _insert(db_session, url="https://example.com/title-match", title="Ethereum surges on ETF news")

    results, total = await search_news(db_session, "ethereum")

    assert total == 2
    assert results[0].url == "https://example.com/title-match"


@pytest.mark.asyncio
async def test_search_news_excludes_non_published_articles(db_session):
    await _insert(
        db_session, url="https://example.com/pending", title="Bitcoin news", editorial_status="PENDING_REVIEW"
    )
    await _insert(
        db_session, url="https://example.com/published", title="Bitcoin news", editorial_status="PUBLISHED"
    )

    results, total = await search_news(db_session, "bitcoin")

    assert total == 1
    assert results[0].url == "https://example.com/published"


@pytest.mark.asyncio
async def test_search_news_filters_by_topic_and_paginates(db_session):
    for i in range(3):
        await _insert(db_session, url=f"https://example.com/crypto-{i}", title="Bitcoin update", portal_topic="CRYPTO")
    await _insert(db_session, url="https://example.com/ai-1", title="Bitcoin mentioned in AI story", portal_topic="AI")

    crypto_only, crypto_total = await search_news(db_session, "bitcoin", topic="CRYPTO")
    assert crypto_total == 3
    assert all(a.portal_topic == "CRYPTO" for a in crypto_only)

    page1, total = await search_news(db_session, "bitcoin", limit=2, offset=0)
    page2, _ = await search_news(db_session, "bitcoin", limit=2, offset=2)
    assert total == 4
    assert len(page1) == 2
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_get_trending_news_ranks_by_importance_score(db_session):
    await _insert(db_session, url="https://example.com/low-impact", title="Minor update", impact=10.0)
    await _insert(db_session, url="https://example.com/high-impact", title="Major breaking news", impact=90.0)

    trending = await get_trending_news(db_session)

    assert [a.url for a in trending] == [
        "https://example.com/high-impact",
        "https://example.com/low-impact",
    ]


@pytest.mark.asyncio
async def test_get_trending_news_excludes_stale_articles(db_session):
    stale_timestamp = int(datetime.now(UTC).timestamp()) - 72 * 3600
    await _insert(db_session, url="https://example.com/stale", impact=90.0, published_at=stale_timestamp)
    await _insert(db_session, url="https://example.com/fresh", impact=10.0)

    trending = await get_trending_news(db_session)

    assert [a.url for a in trending] == ["https://example.com/fresh"]


@pytest.mark.asyncio
async def test_get_trending_news_collapses_a_news_event_to_its_primary_article(db_session):
    primary = await _insert_and_fetch(db_session, url="https://example.com/primary", impact=60.0)
    secondary = await _insert_and_fetch(db_session, url="https://example.com/secondary", impact=40.0)

    event = NewsEvent(title=primary.title, importance_score=9.0, primary_article_id=primary.id)
    db_session.add(event)
    await db_session.flush()
    primary.news_event_id = event.id
    secondary.news_event_id = event.id
    await db_session.commit()

    await _insert(db_session, url="https://example.com/solo", title="Solo story", impact=5.0)

    trending = await get_trending_news(db_session)

    urls = [a.url for a in trending]
    assert urls[0] == "https://example.com/primary"
    assert "https://example.com/secondary" not in urls


@pytest.mark.asyncio
async def test_get_trending_news_excludes_non_published_articles(db_session):
    await _insert(db_session, url="https://example.com/pending", impact=90.0, editorial_status="PENDING_REVIEW")
    await _insert(db_session, url="https://example.com/published", impact=10.0)

    trending = await get_trending_news(db_session)

    assert [a.url for a in trending] == ["https://example.com/published"]


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
async def test_get_portal_news_page_excludes_non_published_articles(db_session):
    await _insert(db_session, url="https://example.com/pending", editorial_status="PENDING_REVIEW")
    await _insert(db_session, url="https://example.com/published", editorial_status="PUBLISHED")

    articles, total = await get_portal_news_page(db_session)

    assert total == 1
    assert articles[0].url == "https://example.com/published"


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


@pytest.mark.asyncio
async def test_get_unprocessed_articles_returns_articles_without_ai_summary(db_session):
    await _insert(db_session, url="https://example.com/unprocessed")

    unprocessed = await get_unprocessed_articles(db_session)

    assert len(unprocessed) == 1
    assert unprocessed[0].ai_summary is None


@pytest.mark.asyncio
async def test_get_unprocessed_articles_excludes_already_processed_articles(db_session):
    await _insert(db_session, url="https://example.com/processed")
    articles, _ = await get_portal_news_page(db_session, limit=1)
    articles[0].ai_summary = "Already processed."
    await db_session.commit()

    unprocessed = await get_unprocessed_articles(db_session)

    assert unprocessed == []


@pytest.mark.asyncio
async def test_get_unprocessed_articles_respects_the_limit(db_session):
    for i in range(3):
        await _insert(db_session, url=f"https://example.com/batch-{i}")

    unprocessed = await get_unprocessed_articles(db_session, limit=2)

    assert len(unprocessed) == 2
