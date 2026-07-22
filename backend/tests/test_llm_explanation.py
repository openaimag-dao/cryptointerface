import numpy as np
import pytest

from app.core.config import get_settings
from app.intelligence.llm import explanation as explanation_module
from app.intelligence.llm.explanation import (
    NOT_CONFIGURED_SUMMARY,
    UPSTREAM_ERROR_SUMMARY,
    build_llm_explanation,
)
from app.services.binance.rest_client import KlineData
from app.services.market_repository import upsert_candle


class _FakeToolUseBlock:
    def __init__(self, input_data: dict) -> None:
        self.type = "tool_use"
        self.input = input_data


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, content: list) -> None:
        self.content = content


class _FakeMessages:
    def __init__(self, calls: list[dict], response: _FakeResponse) -> None:
        self._calls = calls
        self._response = response

    async def create(self, **kwargs) -> _FakeResponse:
        self._calls.append(kwargs)
        return self._response


class _FakeAsyncAnthropic:
    calls: list[dict] = []
    response: _FakeResponse | None = None

    def __init__(self, api_key: str) -> None:
        self.messages = _FakeMessages(_FakeAsyncAnthropic.calls, _FakeAsyncAnthropic.response)

    async def close(self) -> None:
        pass


class _RaisingMessages:
    async def create(self, **kwargs):
        import anthropic
        import httpx

        raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


class _RaisingAsyncAnthropic:
    def __init__(self, api_key: str) -> None:
        self.messages = _RaisingMessages()

    async def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def _reset_fake_calls():
    _FakeAsyncAnthropic.calls = []
    yield


async def _insert_candles(db_session, symbol: str, n: int = 260) -> None:
    base_time = 1_700_000_000_000
    closes = np.linspace(100, 160, n) + np.sin(np.linspace(0, 20, n)) * 0.5
    for i in range(n):
        kline = KlineData(
            open_time=base_time + i * 3_600_000,
            close_time=base_time + i * 3_600_000 + 3_599_999,
            open=float(closes[i]),
            high=float(closes[i]) + 0.5,
            low=float(closes[i]) - 0.5,
            close=float(closes[i]),
            volume=1_000.0,
            quote_volume=100_000.0,
            trades=50,
        )
        await upsert_candle(db_session, symbol, "1h", kline, is_closed=True)


@pytest.mark.asyncio
async def test_build_llm_explanation_returns_none_without_candle_history(db_session):
    result = await build_llm_explanation(db_session, "NOSUCHUSDT", "1h")
    assert result is None


@pytest.mark.asyncio
async def test_build_llm_explanation_without_api_key_falls_back(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    await _insert_candles(db_session, "TESTUSDT")

    result = await build_llm_explanation(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.summary == NOT_CONFIGURED_SUMMARY
    assert result.direction in ("LONG", "SHORT", "WAIT")
    assert result.key_drivers  # falls back to the engine's own reasons


@pytest.mark.asyncio
async def test_build_llm_explanation_uses_forced_tool_choice_and_preserves_direction_confidence(
    monkeypatch, db_session
):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(explanation_module.anthropic, "AsyncAnthropic", _FakeAsyncAnthropic)
    _FakeAsyncAnthropic.response = _FakeResponse(
        [
            _FakeToolUseBlock(
                {
                    "summary": "Test summary grounded in the given facts.",
                    "key_drivers": ["driver one"],
                    "risks": ["risk one"],
                    "opportunities": ["opportunity one"],
                    "assets_affected": ["TESTUSDT"],
                }
            )
        ]
    )
    await _insert_candles(db_session, "TESTUSDT")

    result = await build_llm_explanation(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.summary == "Test summary grounded in the given facts."
    assert result.key_drivers == ["driver one"]
    assert result.risks == ["risk one"]
    assert result.opportunities == ["opportunity one"]
    assert result.assets_affected == ["TESTUSDT"]

    assert len(_FakeAsyncAnthropic.calls) == 1
    call = _FakeAsyncAnthropic.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": "emit_explanation"}
    assert call["tools"][0]["name"] == "emit_explanation"


@pytest.mark.asyncio
async def test_build_llm_explanation_handles_upstream_error_gracefully(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(explanation_module.anthropic, "AsyncAnthropic", _RaisingAsyncAnthropic)
    await _insert_candles(db_session, "TESTUSDT")

    result = await build_llm_explanation(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.summary == UPSTREAM_ERROR_SUMMARY
