from datetime import UTC, datetime

import pytest

from app.core.config import get_settings
from app.intelligence.llm import news_translation
from app.intelligence.llm.news_translation import build_news_translation
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
async def test_build_news_translation_returns_none_without_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    result = await build_news_translation(_article(), "ru")

    assert result is None


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_for_unsupported_language(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    result = await build_news_translation(_article(), "fr")

    assert result is None


@pytest.mark.asyncio
async def test_build_news_translation_returns_translated_title_and_summary(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    calls: list[dict] = []
    reply = {
        "title": "OpenAI выпускает новую флагманскую модель ИИ",
        "summary": "OpenAI анонсировала новую модель с улучшенными рассуждениями.",
    }
    monkeypatch.setattr(news_translation, "generate_structured", _fake_generate_structured(calls, reply))

    result = await build_news_translation(_article(), "ru")

    assert result is not None
    assert result.title == "OpenAI выпускает новую флагманскую модель ИИ"
    assert result.summary == "OpenAI анонсировала новую модель с улучшенными рассуждениями."

    call = calls[0]
    assert "Russian" in call["user_message"]


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_on_upstream_error(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(news_translation, "generate_structured", _fake_generate_structured([], None))

    result = await build_news_translation(_article(), "ru")

    assert result is None


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_for_blank_reply(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        news_translation, "generate_structured", _fake_generate_structured([], {"title": "", "summary": ""})
    )

    result = await build_news_translation(_article(), "ru")

    assert result is None
