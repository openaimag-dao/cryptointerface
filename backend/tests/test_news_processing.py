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
        "summary": "OpenAI released a new model with better reasoning.",
        "entities": [{"name": "OpenAI", "type": "COMPANY"}],
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
async def test_build_news_processing_returns_none_without_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")

    result = await build_news_processing(_article())

    assert result is None


@pytest.mark.asyncio
async def test_build_news_processing_returns_summary_and_entities(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(news_processing.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)

    result = await build_news_processing(_article())

    assert result is not None
    assert result.summary == "OpenAI released a new model with better reasoning."
    assert len(result.entities) == 1
    assert result.entities[0].name == "OpenAI"
    assert result.entities[0].entity_type == "COMPANY"

    call = _FakeAsyncAnthropic.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "emit_processing"}


@pytest.mark.asyncio
async def test_build_news_processing_filters_out_invalid_entity_types(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    _FakeAsyncAnthropic.reply = {
        "summary": "Some summary.",
        "entities": [{"name": "OpenAI", "type": "COMPANY"}, {"name": "Bad", "type": "NOT_A_REAL_TYPE"}],
    }
    monkeypatch.setattr(news_processing.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)

    result = await build_news_processing(_article())

    assert result is not None
    assert len(result.entities) == 1
    assert result.entities[0].name == "OpenAI"


@pytest.mark.asyncio
async def test_build_news_processing_returns_none_on_upstream_error(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(news_processing.anthropic, "AsyncAnthropic", _RaisingAsyncAnthropic)

    result = await build_news_processing(_article())

    assert result is None
