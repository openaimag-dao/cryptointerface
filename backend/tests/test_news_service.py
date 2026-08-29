from datetime import UTC, datetime

import pytest

from app.intelligence.news import service
from app.intelligence.news.fetcher import RawNewsEntry
from app.intelligence.news.service import fetch_and_persist_news
from app.models.news_source import NewsSource
from app.services.news_repository import get_latest_news
from app.services.news_source_repository import get_source_by_id


def _entry(url: str, title: str = "Bitcoin rallies") -> RawNewsEntry:
    return RawNewsEntry(
        source="Test Source",
        title=title,
        summary="Summary text",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
    )


@pytest.mark.asyncio
async def test_fetch_and_persist_news_only_polls_enabled_sources(db_session, monkeypatch):
    enabled = NewsSource(source_key="on", name="On", rss_url="https://example.com/on", enabled=True)
    disabled = NewsSource(source_key="off", name="Off", rss_url="https://example.com/off", enabled=False)
    db_session.add_all([enabled, disabled])
    await db_session.commit()

    polled_source_keys: list[str] = []

    async def fake_fetch_source(source_def):
        polled_source_keys.append(source_def.id)
        return [_entry(f"https://example.com/{source_def.id}/1")]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)

    new_count = await fetch_and_persist_news(db_session)

    assert polled_source_keys == ["on"]
    assert new_count == 1


@pytest.mark.asyncio
async def test_fetch_and_persist_news_publishes_directly_for_auto_publish_sources(db_session, monkeypatch):
    source = NewsSource(source_key="auto", name="Auto", rss_url="https://example.com/auto", auto_publish=True)
    db_session.add(source)
    await db_session.commit()

    async def fake_fetch_source(source_def):
        return [_entry("https://example.com/auto/1")]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)
    await fetch_and_persist_news(db_session)

    articles = await get_latest_news(db_session, limit=10)
    assert articles[0].editorial_status == "PUBLISHED"
    assert articles[0].slug is not None


@pytest.mark.asyncio
async def test_fetch_and_persist_news_sends_manual_review_sources_to_pending(db_session, monkeypatch):
    source = NewsSource(source_key="manual", name="Manual", rss_url="https://example.com/manual", auto_publish=False)
    db_session.add(source)
    await db_session.commit()

    async def fake_fetch_source(source_def):
        return [_entry("https://example.com/manual/1")]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)
    await fetch_and_persist_news(db_session)

    articles = await get_latest_news(db_session, limit=10)
    assert articles[0].editorial_status == "PENDING_REVIEW"


@pytest.mark.asyncio
async def test_fetch_and_persist_news_records_fetch_result_per_source(db_session, monkeypatch):
    source = NewsSource(source_key="logged", name="Logged", rss_url="https://example.com/logged")
    db_session.add(source)
    await db_session.commit()

    async def fake_fetch_source(source_def):
        return [_entry("https://example.com/logged/1"), _entry("https://example.com/logged/2")]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)
    await fetch_and_persist_news(db_session)

    refreshed = await get_source_by_id(db_session, source.id)
    assert refreshed.last_status == "SUCCESS"
    assert refreshed.articles_imported_count == 2


@pytest.mark.asyncio
async def test_fetch_and_persist_news_groups_multi_source_coverage_into_one_event(db_session, monkeypatch):
    source_a = NewsSource(source_key="wire-a", name="Wire A", rss_url="https://example.com/wire-a")
    source_b = NewsSource(source_key="wire-b", name="Wire B", rss_url="https://example.com/wire-b")
    db_session.add_all([source_a, source_b])
    await db_session.commit()

    async def fake_fetch_source(source_def):
        if source_def.id == "wire-a":
            return [_entry("https://example.com/wire-a/1", title="OpenAI launches new flagship AI model")]
        return [_entry("https://example.com/wire-b/1", title="OpenAI unveils new flagship AI model to the public")]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)
    await fetch_and_persist_news(db_session)

    articles = await get_latest_news(db_session, limit=10)
    assert len(articles) == 2
    assert articles[0].news_event_id is not None
    assert articles[0].news_event_id == articles[1].news_event_id


@pytest.mark.asyncio
async def test_fetch_and_persist_news_leaves_unrelated_articles_ungrouped(db_session, monkeypatch):
    source = NewsSource(source_key="solo", name="Solo", rss_url="https://example.com/solo")
    db_session.add(source)
    await db_session.commit()

    async def fake_fetch_source(source_def):
        return [
            _entry("https://example.com/solo/1", title="OpenAI launches new flagship AI model"),
            _entry("https://example.com/solo/2", title="Robotics startup raises Series A funding"),
        ]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)
    await fetch_and_persist_news(db_session)

    articles = await get_latest_news(db_session, limit=10)
    assert all(a.news_event_id is None for a in articles)


@pytest.mark.asyncio
async def test_fetch_and_persist_news_records_error_without_stopping_other_sources(db_session, monkeypatch):
    failing = NewsSource(source_key="failing", name="Failing", rss_url="https://example.com/failing")
    healthy = NewsSource(source_key="healthy", name="Healthy", rss_url="https://example.com/healthy")
    db_session.add_all([failing, healthy])
    await db_session.commit()

    async def fake_fetch_source(source_def):
        if source_def.id == "failing":
            raise RuntimeError("boom")
        return [_entry("https://example.com/healthy/1")]

    monkeypatch.setattr(service, "fetch_source", fake_fetch_source)
    new_count = await fetch_and_persist_news(db_session)

    assert new_count == 1
    failing_refreshed = await get_source_by_id(db_session, failing.id)
    assert failing_refreshed.last_status == "ERROR"
    assert failing_refreshed.last_error == "boom"
    healthy_refreshed = await get_source_by_id(db_session, healthy.id)
    assert healthy_refreshed.last_status == "SUCCESS"
