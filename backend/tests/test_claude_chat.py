import pytest

from app.core.config import get_settings
from app.services import claude_chat
from app.services.claude_chat import (
    NOT_CONFIGURED_MESSAGE,
    UPSTREAM_ERROR_MESSAGE,
    ChatTurn,
    build_watchlist_snapshot,
    send_chat_message,
)


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [_FakeTextBlock(text)]


class _FakeMessages:
    def __init__(self, calls: list[dict], reply: str) -> None:
        self._calls = calls
        self._reply = reply

    async def create(self, **kwargs) -> _FakeResponse:
        self._calls.append(kwargs)
        return _FakeResponse(self._reply)


class _FakeAsyncAnthropic:
    calls: list[dict] = []
    reply = "Hello from Claude"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.messages = _FakeMessages(_FakeAsyncAnthropic.calls, _FakeAsyncAnthropic.reply)

    async def close(self) -> None:
        pass


class _RaisingAsyncAnthropic(_FakeAsyncAnthropic):
    def __init__(self, api_key: str) -> None:
        super().__init__(api_key)
        self.messages = _RaisingMessages()


class _RaisingMessages:
    async def create(self, **kwargs):
        import anthropic
        import httpx

        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


@pytest.fixture(autouse=True)
def _reset_fake_calls():
    _FakeAsyncAnthropic.calls = []
    yield


@pytest.mark.asyncio
async def test_send_chat_message_without_api_key_returns_not_configured(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")

    result = await send_chat_message("What's the BTC price?", [])

    assert result == NOT_CONFIGURED_MESSAGE


@pytest.mark.asyncio
async def test_send_chat_message_sends_history_and_returns_text(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(claude_chat.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)

    history = [ChatTurn(role="user", content="hi"), ChatTurn(role="assistant", content="hello")]
    result = await send_chat_message("What's the BTC price?", history)

    assert result == "Hello from Claude"
    assert len(_FakeAsyncAnthropic.calls) == 1
    call = _FakeAsyncAnthropic.calls[0]
    assert call["messages"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "What's the BTC price?"},
    ]
    assert call["model"] == settings.anthropic_chat_model
    assert "no live market data available" in call["system"].lower()


@pytest.mark.asyncio
async def test_send_chat_message_handles_upstream_error_gracefully(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(claude_chat.anthropic, "AsyncAnthropic", _RaisingAsyncAnthropic)

    result = await send_chat_message("hello", [])

    assert result == UPSTREAM_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_build_watchlist_snapshot_with_no_candles_says_no_data(db_session):
    snapshot = await build_watchlist_snapshot()

    assert snapshot == "No live market data available yet for the watchlist."


@pytest.mark.asyncio
async def test_build_watchlist_snapshot_includes_symbol_with_candles(db_session):
    from app.services.binance.rest_client import KlineData
    from app.services.market_repository import upsert_candle

    settings = get_settings()
    symbol = settings.symbol_list[0]

    base_time = 1_700_000_000_000
    for i in range(210):
        kline = KlineData(
            open_time=base_time + i * 3_600_000,
            close_time=base_time + i * 3_600_000 + 3_599_999,
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1_000.0,
            quote_volume=100_000.0,
            trades=50,
        )
        await upsert_candle(db_session, symbol, "1h", kline, is_closed=True)

    snapshot = await build_watchlist_snapshot()

    assert "Current watchlist snapshot" in snapshot
    assert symbol in snapshot
    assert "direction" in snapshot
