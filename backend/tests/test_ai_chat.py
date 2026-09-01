import pytest

from app.core.config import get_settings
from app.services import ai_chat
from app.services.ai_chat import (
    NOT_CONFIGURED_MESSAGE,
    UPSTREAM_ERROR_MESSAGE,
    ChatTurn,
    build_watchlist_snapshot,
    send_chat_message,
)


def _fake_generate_text(calls: list[dict], reply: str | None):
    async def _generate_text(**kwargs) -> str | None:
        calls.append(kwargs)
        return reply

    return _generate_text


@pytest.mark.asyncio
async def test_send_chat_message_without_api_key_returns_not_configured(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    result = await send_chat_message("What's the BTC price?", [])

    assert result == NOT_CONFIGURED_MESSAGE


@pytest.mark.asyncio
async def test_send_chat_message_sends_history_and_returns_text(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    calls: list[dict] = []
    monkeypatch.setattr(ai_chat, "generate_text", _fake_generate_text(calls, "Hello from Gemini"))

    history = [ChatTurn(role="user", content="hi"), ChatTurn(role="assistant", content="hello")]
    result = await send_chat_message("What's the BTC price?", history)

    assert result == "Hello from Gemini"
    assert len(calls) == 1
    call = calls[0]
    assert call["messages"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "What's the BTC price?"},
    ]
    assert "no live market data available" in call["system_prompt"].lower()


@pytest.mark.asyncio
async def test_send_chat_message_handles_upstream_error_gracefully(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(ai_chat, "generate_text", _fake_generate_text([], None))

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
