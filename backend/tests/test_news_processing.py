from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.intelligence.llm import news_processing
from app.intelligence.llm.news_processing import build_news_processing
from app.models.news import NewsArticle


def _article() -> NewsArticle:
    article = NewsArticle(
        source="Test",
        title="OpenAI launches new flagship AI model",
        summary="OpenAI announced a new model with improved reasoning.",
        url="https://example.com/a",
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
    )
    article.id = 1
    return article


def _fake_generate_structured(calls: list[dict], reply: dict | None):
    async def _generate_structured(**kwargs) -> dict | None:
        calls.append(kwargs)
        return reply

    return _generate_structured


@pytest.mark.asyncio
async def test_build_news_processing_returns_none_without_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    result = await build_news_processing(_article())

    assert result is None


@pytest.mark.asyncio
async def test_build_news_processing_returns_summary_and_entities(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    calls: list[dict] = []
    reply = {
        "summary": "OpenAI released a new model with better reasoning.",
        "entities": [{"name": "OpenAI", "type": "COMPANY"}],
    }
    monkeypatch.setattr(news_processing, "generate_structured", _fake_generate_structured(calls, reply))

    result = await build_news_processing(_article())

    assert result is not None
    assert result.summary == "OpenAI released a new model with better reasoning."
    assert len(result.entities) == 1
    assert result.entities[0].name == "OpenAI"
    assert result.entities[0].entity_type == "COMPANY"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_build_news_processing_filters_out_invalid_entity_types(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    reply = {
        "summary": "Some summary.",
        "entities": [{"name": "OpenAI", "type": "COMPANY"}, {"name": "Bad", "type": "NOT_A_REAL_TYPE"}],
    }
    monkeypatch.setattr(news_processing, "generate_structured", _fake_generate_structured([], reply))

    result = await build_news_processing(_article())

    assert result is not None
    assert len(result.entities) == 1
    assert result.entities[0].name == "OpenAI"


@pytest.mark.asyncio
async def test_build_news_processing_returns_none_on_upstream_error(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(news_processing, "generate_structured", _fake_generate_structured([], None))

    result = await build_news_processing(_article())

    assert result is None
