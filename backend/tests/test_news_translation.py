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


class _FakeToolUseBlock:
    def __init__(self, input_dict: dict) -> None:
        self.type = "tool_use"
        self.input = input_dict


class _FakeResponse:
    def __init__(self, input_dict: dict) -> None:
        self.content = [_FakeToolUseBlock(input_dict)]


class _FakeMessages:
    def __init__(self, calls: list[dict], reply: dict) -> None:
        self._calls = calls
        self._reply = reply

    async def create(self, **kwargs) -> _FakeResponse:
        self._calls.append(kwargs)
        return _FakeResponse(self._reply)


class _FakeAsyncAnthropic:
    calls: list[dict] = []
    reply: dict = {
        "title": "OpenAI выпускает новую флагманскую модель ИИ",
        "summary": "OpenAI анонсировала новую модель с улучшенными рассуждениями.",
    }

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.messages = _FakeMessages(_FakeAsyncAnthropic.calls, _FakeAsyncAnthropic.reply)

    async def close(self) -> None:
        pass


class _RaisingMessages:
    async def create(self, **kwargs):
        import anthropic
        import httpx

        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


class _RaisingAsyncAnthropic(_FakeAsyncAnthropic):
    def __init__(self, api_key: str) -> None:
        super().__init__(api_key)
        self.messages = _RaisingMessages()


@pytest.fixture(autouse=True)
def _reset_fake_calls():
    _FakeAsyncAnthropic.calls = []
    yield


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_without_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")

    result = await build_news_translation(_article(), "ru")

    assert result is None


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_for_unsupported_language(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")

    result = await build_news_translation(_article(), "fr")

    assert result is None


@pytest.mark.asyncio
async def test_build_news_translation_returns_translated_title_and_summary(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(news_translation.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)

    result = await build_news_translation(_article(), "ru")

    assert result is not None
    assert result.title == "OpenAI выпускает новую флагманскую модель ИИ"
    assert result.summary == "OpenAI анонсировала новую модель с улучшенными рассуждениями."

    call = _FakeAsyncAnthropic.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "emit_translation"}
    assert "Russian" in call["messages"][0]["content"]


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_on_upstream_error(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(news_translation.anthropic, "AsyncAnthropic", _RaisingAsyncAnthropic)

    result = await build_news_translation(_article(), "ru")

    assert result is None


@pytest.mark.asyncio
async def test_build_news_translation_returns_none_for_blank_reply(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    _FakeAsyncAnthropic.reply = {"title": "", "summary": ""}
    monkeypatch.setattr(news_translation.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)

    result = await build_news_translation(_article(), "ru")

    assert result is None
