import pytest

from app.intelligence.news.sources import NEWS_SOURCES
from app.models.news_source import NewsSource
from app.services.news_source_repository import (
    get_all_sources,
    get_enabled_sources,
    get_recent_fetch_logs,
    get_source_by_id,
    record_fetch_result,
    seed_default_sources,
    update_source,
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


@pytest.mark.asyncio
async def test_update_source_applies_editable_fields(db_session):
    source = NewsSource(source_key="upd-src", name="Old Name", rss_url="https://example.com/old")
    db_session.add(source)
    await db_session.commit()

    updated = await update_source(db_session, source, {"name": "New Name", "enabled": False, "trust_score": 42.0})

    assert updated.name == "New Name"
    assert updated.enabled is False
    assert updated.trust_score == 42.0


@pytest.mark.asyncio
async def test_update_source_ignores_none_values_and_unknown_keys(db_session):
    source = NewsSource(source_key="upd-src-2", name="Keep Me", rss_url="https://example.com/keep")
    db_session.add(source)
    await db_session.commit()

    updated = await update_source(db_session, source, {"name": None, "source_key": "hijacked"})

    assert updated.name == "Keep Me"
    assert updated.source_key == "upd-src-2"


@pytest.mark.asyncio
async def test_get_recent_fetch_logs_returns_newest_first(db_session):
    source = NewsSource(source_key="log-src", name="Log Source", rss_url="https://example.com/log")
    db_session.add(source)
    await db_session.commit()

    await record_fetch_result(db_session, source, status="SUCCESS", articles_found=1, articles_new=1, duration_ms=10)
    await record_fetch_result(db_session, source, status="ERROR", articles_found=0, articles_new=0, duration_ms=5)

    logs = await get_recent_fetch_logs(db_session)

    assert len(logs) == 2
    assert logs[0].status == "ERROR"
    assert logs[1].status == "SUCCESS"


@pytest.mark.asyncio
async def test_get_recent_fetch_logs_filters_by_source(db_session):
    source_a = NewsSource(source_key="log-a", name="A", rss_url="https://example.com/a")
    source_b = NewsSource(source_key="log-b", name="B", rss_url="https://example.com/b")
    db_session.add_all([source_a, source_b])
    await db_session.commit()

    await record_fetch_result(db_session, source_a, status="SUCCESS", articles_found=1, articles_new=1, duration_ms=1)
    await record_fetch_result(db_session, source_b, status="SUCCESS", articles_found=1, articles_new=1, duration_ms=1)

    logs = await get_recent_fetch_logs(db_session, source_id=source_a.id)

    assert len(logs) == 1
    assert logs[0].source_id == source_a.id
