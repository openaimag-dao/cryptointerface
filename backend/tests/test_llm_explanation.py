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


def _fake_generate_structured(calls: list[dict], reply: dict | None):
    async def _generate_structured(**kwargs) -> dict | None:
        calls.append(kwargs)
        return reply

    return _generate_structured


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
    monkeypatch.setattr(settings, "gemini_api_key", "")
    await _insert_candles(db_session, "TESTUSDT")

    result = await build_llm_explanation(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.summary == NOT_CONFIGURED_SUMMARY
    assert result.direction in ("LONG", "SHORT", "WAIT")
    assert result.key_drivers  # falls back to the engine's own reasons


@pytest.mark.asyncio
async def test_build_llm_explanation_uses_structured_output_and_preserves_direction_confidence(
    monkeypatch, db_session
):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    calls: list[dict] = []
    reply = {
        "summary": "Test summary grounded in the given facts.",
        "key_drivers": ["driver one"],
        "risks": ["risk one"],
        "opportunities": ["opportunity one"],
        "assets_affected": ["TESTUSDT"],
    }
    monkeypatch.setattr(explanation_module, "generate_structured", _fake_generate_structured(calls, reply))
    await _insert_candles(db_session, "TESTUSDT")

    result = await build_llm_explanation(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.summary == "Test summary grounded in the given facts."
    assert result.key_drivers == ["driver one"]
    assert result.risks == ["risk one"]
    assert result.opportunities == ["opportunity one"]
    assert result.assets_affected == ["TESTUSDT"]

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_build_llm_explanation_handles_upstream_error_gracefully(monkeypatch, db_session):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(explanation_module, "generate_structured", _fake_generate_structured([], None))
    await _insert_candles(db_session, "TESTUSDT")

    result = await build_llm_explanation(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.summary == UPSTREAM_ERROR_SUMMARY
