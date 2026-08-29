import pytest

from app.intelligence.news.sources import NEWS_SOURCES
from app.models.news_source import NewsSource
from app.services.news_source_repository import (
    get_all_sources,
    get_enabled_sources,
    get_source_by_id,
    record_fetch_result,
    seed_default_sources,
)


@pytest.mark.asyncio
async def test_seed_default_sources_inserts_every_static_source(db_session):
    await seed_default_sources(db_session)

    sources = await get_all_sources(db_session)
    assert len(sources) == len(NEWS_SOURCES)
    assert {s.source_key for s in sources} == {s.id for s in NEWS_SOURCES}


@pytest.mark.asyncio
async def test_seed_default_sources_is_idempotent(db_session):
    await seed_default_sources(db_session)
    await seed_default_sources(db_session)

    sources = await get_all_sources(db_session)
    assert len(sources) == len(NEWS_SOURCES)


@pytest.mark.asyncio
async def test_seed_never_overwrites_an_admin_edited_row(db_session):
    await seed_default_sources(db_session)
    sources = await get_all_sources(db_session)
    edited = sources[0]
    edited.enabled = False
    edited.trust_score = 12.0
    await db_session.commit()

    await seed_default_sources(db_session)

    refreshed = await get_source_by_id(db_session, edited.id)
    assert refreshed is not None
    assert refreshed.enabled is False
    assert refreshed.trust_score == 12.0


@pytest.mark.asyncio
async def test_get_enabled_sources_excludes_disabled(db_session):
    await seed_default_sources(db_session)
    all_sources = await get_all_sources(db_session)
    all_sources[0].enabled = False
    await db_session.commit()

    enabled = await get_enabled_sources(db_session)

    assert len(enabled) == len(all_sources) - 1
    assert all(s.enabled for s in enabled)


@pytest.mark.asyncio
async def test_to_source_def_round_trips_fields(db_session):
    await seed_default_sources(db_session)
    sources = await get_all_sources(db_session)
    source_def = sources[0].to_source_def()

    assert source_def.id == sources[0].source_key
    assert source_def.rss_url == sources[0].rss_url
    assert source_def.default_topic == sources[0].default_topic


@pytest.mark.asyncio
async def test_record_fetch_result_updates_source_and_creates_log(db_session):
    source = NewsSource(source_key="test-src", name="Test Source", rss_url="https://example.com/rss")
    db_session.add(source)
    await db_session.commit()

    await record_fetch_result(
        db_session, source, status="SUCCESS", articles_found=5, articles_new=3, duration_ms=120
    )

    refreshed = await get_source_by_id(db_session, source.id)
    assert refreshed.last_status == "SUCCESS"
    assert refreshed.last_error is None
    assert refreshed.articles_imported_count == 3
    assert refreshed.last_fetched_at is not None


@pytest.mark.asyncio
async def test_record_fetch_result_accumulates_articles_imported_count(db_session):
    source = NewsSource(source_key="test-src-2", name="Test Source 2", rss_url="https://example.com/rss2")
    db_session.add(source)
    await db_session.commit()

    await record_fetch_result(db_session, source, status="SUCCESS", articles_found=2, articles_new=2, duration_ms=10)
    await record_fetch_result(db_session, source, status="SUCCESS", articles_found=1, articles_new=1, duration_ms=10)

    refreshed = await get_source_by_id(db_session, source.id)
    assert refreshed.articles_imported_count == 3


@pytest.mark.asyncio
async def test_record_fetch_result_records_error(db_session):
    source = NewsSource(source_key="test-src-3", name="Test Source 3", rss_url="https://example.com/rss3")
    db_session.add(source)
    await db_session.commit()

    await record_fetch_result(
        db_session, source, status="ERROR", articles_found=0, articles_new=0, duration_ms=5, error_message="timeout"
    )

    refreshed = await get_source_by_id(db_session, source.id)
    assert refreshed.last_status == "ERROR"
    assert refreshed.last_error == "timeout"
