from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.intelligence.llm import news_digest
from app.intelligence.llm.news_digest import (
    NOT_CONFIGURED_SUMMARY,
    UPSTREAM_ERROR_SUMMARY,
    build_news_digest,
)
from app.services.news_repository import insert_article


async def _insert(db_session, *, url: str, title: str = "Title", topic: str = "AI"):
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
        portal_topic=topic,
    )


def _fake_generate_structured(calls: list[dict], reply: dict | None):
    async def _generate_structured(**kwargs) -> dict | None:
        calls.append(kwargs)
        return reply

    return _generate_structured


@pytest.mark.asyncio
async def test_build_news_digest_returns_none_without_any_articles(db_session):
    result = await build_news_digest(db_session, "AI")
    assert result is None


@pytest.mark.asyncio
async def test_build_news_digest_without_api_key_returns_fallback(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")
    await _insert(db_session, url="https://example.com/a", topic="AI")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.summary == NOT_CONFIGURED_SUMMARY
    assert result.highlights == []
    assert result.article_count == 1


@pytest.mark.asyncio
async def test_build_news_digest_only_considers_the_given_topic(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")
    await _insert(db_session, url="https://example.com/ai", topic="AI")
    await _insert(db_session, url="https://example.com/crypto", topic="CRYPTO")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.article_count == 1


@pytest.mark.asyncio
async def test_build_news_digest_success_returns_summary_and_highlights(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    calls: list[dict] = []
    reply = {"summary": "AI is moving fast.", "highlights": ["Thing one happened", "Thing two happened"]}
    monkeypatch.setattr(news_digest, "generate_structured", _fake_generate_structured(calls, reply))
    await _insert(db_session, url="https://example.com/a", topic="AI")
    await _insert(db_session, url="https://example.com/b", topic="AI")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.summary == "AI is moving fast."
    assert result.highlights == ["Thing one happened", "Thing two happened"]
    assert result.article_count == 2
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_build_news_digest_handles_upstream_error_gracefully(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(news_digest, "generate_structured", _fake_generate_structured([], None))
    await _insert(db_session, url="https://example.com/a", topic="AI")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.summary == UPSTREAM_ERROR_SUMMARY
