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
    reply: dict = {"summary": "AI is moving fast.", "highlights": ["Thing one happened", "Thing two happened"]}

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
async def test_build_news_digest_returns_none_without_any_articles(db_session):
    result = await build_news_digest(db_session, "AI")
    assert result is None


@pytest.mark.asyncio
async def test_build_news_digest_without_api_key_returns_fallback(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    await _insert(db_session, url="https://example.com/a", topic="AI")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.summary == NOT_CONFIGURED_SUMMARY
    assert result.highlights == []
    assert result.article_count == 1


@pytest.mark.asyncio
async def test_build_news_digest_only_considers_the_given_topic(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    await _insert(db_session, url="https://example.com/ai", topic="AI")
    await _insert(db_session, url="https://example.com/crypto", topic="CRYPTO")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.article_count == 1


@pytest.mark.asyncio
async def test_build_news_digest_success_returns_summary_and_highlights(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(news_digest.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)
    await _insert(db_session, url="https://example.com/a", topic="AI")
    await _insert(db_session, url="https://example.com/b", topic="AI")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.summary == "AI is moving fast."
    assert result.highlights == ["Thing one happened", "Thing two happened"]
    assert result.article_count == 2

    call = _FakeAsyncAnthropic.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "emit_digest"}
    assert call["model"] == settings.anthropic_chat_model


@pytest.mark.asyncio
async def test_build_news_digest_handles_upstream_error_gracefully(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(news_digest.anthropic, "AsyncAnthropic", _RaisingAsyncAnthropic)
    await _insert(db_session, url="https://example.com/a", topic="AI")

    result = await build_news_digest(db_session, "AI")

    assert result is not None
    assert result.summary == UPSTREAM_ERROR_SUMMARY
