import time

import numpy as np
import pytest

from app.services.asset_service import (
    get_asset_summary,
    get_derivatives_snapshot,
    get_macro_snapshot,
    get_news_snapshot,
    get_overview_snapshot,
    get_sentiment_snapshot,
    get_technical_snapshot,
    get_whales_snapshot,
    to_base_asset,
    to_trading_pair,
)
from app.services.binance.rest_client import KlineData
from app.services.market_repository import (
    insert_funding,
    insert_liquidation,
    insert_open_interest,
    upsert_candle,
    upsert_market_stat,
)
from app.services.news_repository import insert_article
from app.services.whale_repository import insert_whale_event


def test_to_trading_pair_appends_usdt():
    assert to_trading_pair("btc") == "BTCUSDT"
    assert to_trading_pair("ETH") == "ETHUSDT"


def test_to_base_asset_strips_usdt_suffix():
    assert to_base_asset("BTCUSDT") == "BTC"
    assert to_base_asset("btcusdt") == "BTC"


def test_to_base_asset_passthrough_when_no_usdt_suffix():
    assert to_base_asset("BTC") == "BTC"


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
async def test_get_asset_summary_returns_none_without_market_stat(db_session):
    summary = await get_asset_summary(db_session, "NOPE")
    assert summary is None


@pytest.mark.asyncio
async def test_get_asset_summary_combines_stat_funding_oi_and_decision(db_session):
    await upsert_market_stat(db_session, "TESTUSDT", 150.0, 2.5, 155.0, 145.0, 1_000_000.0, 150_000_000.0)
    await insert_funding(db_session, "TESTUSDT", 0.0001, 150.0, 1_700_900_000)
    await insert_open_interest(db_session, "TESTUSDT", 5_000.0, 750_000.0, 1_700_900_000)
    await _insert_candles(db_session, "TESTUSDT")

    summary = await get_asset_summary(db_session, "TEST")

    assert summary is not None
    assert summary.symbol == "TESTUSDT"
    assert summary.base_asset == "TEST"
    assert summary.price == 150.0
    assert summary.funding_rate == 0.0001
    assert summary.open_interest == 5_000.0
    assert summary.direction in ("LONG", "SHORT", "WAIT")
    assert 0.0 <= summary.market_score <= 100.0
    # No CoinGecko mapping for a synthetic symbol -> extended fields stay None.
    assert summary.change_percent_7d is None
    assert summary.market_cap is None


@pytest.mark.asyncio
async def test_get_overview_snapshot_returns_none_without_candles(db_session):
    overview = await get_overview_snapshot(db_session, "NOPE")
    assert overview is None


@pytest.mark.asyncio
async def test_get_overview_snapshot_returns_indicator_subset(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    overview = await get_overview_snapshot(db_session, "TEST")

    assert overview is not None
    assert overview.trend_status in ("LONG", "SHORT", "WAIT")
    assert overview.rsi.name == "RSI (14)"
    assert overview.macd.name == "MACD"
    assert overview.atr.name == "ATR (14)"
    assert overview.ema_alignment.name == "EMA Alignment"
    assert overview.vwap.name == "VWAP"
    assert overview.volume_trend.name == "Volume Trend"
    assert overview.liquidity_score.name == "Liquidity Score"


@pytest.mark.asyncio
async def test_get_technical_snapshot_includes_indicators_and_smart_money(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    technical = await get_technical_snapshot(db_session, "TEST")

    assert technical is not None
    assert len(technical.indicators) == 13
    assert len(technical.smart_money) == 8
    assert technical.breakout_status in ("BROKEN_ABOVE_RESISTANCE", "BROKEN_BELOW_SUPPORT", "INSIDE_RANGE")


@pytest.mark.asyncio
async def test_get_derivatives_snapshot_with_no_data_is_empty_but_not_none(db_session):
    derivatives = await get_derivatives_snapshot(db_session, "NOPE")

    assert derivatives.funding_rate is None
    assert derivatives.open_interest is None
    assert derivatives.liquidation_clusters == []


@pytest.mark.asyncio
async def test_get_derivatives_snapshot_buckets_liquidations_and_computes_oi_delta(db_session):
    await insert_funding(db_session, "TESTUSDT", 0.0002, 150.0, 1_700_900_000)
    await insert_open_interest(db_session, "TESTUSDT", 4_000.0, 600_000.0, 1_700_800_000)
    await insert_open_interest(db_session, "TESTUSDT", 5_000.0, 750_000.0, 1_700_900_000)
    for i in range(10):
        await insert_liquidation(
            db_session,
            "TESTUSDT",
            side="SELL" if i % 2 == 0 else "BUY",
            price=100.0 + i * 5,
            quantity=1.0,
            amount_usd=1_000.0,
            timestamp=1_700_900_000 + i,
        )

    derivatives = await get_derivatives_snapshot(db_session, "TEST")

    assert derivatives.funding_rate == 0.0002
    assert derivatives.oi_delta_percent == pytest.approx(25.0)
    assert sum(c.event_count for c in derivatives.liquidation_clusters) == 10
    assert len(derivatives.liquidation_clusters) <= 6


@pytest.mark.asyncio
async def test_get_derivatives_snapshot_funding_trend_matches_schema_literal(db_session):
    # Two funding readings so `funding_trend` actually takes the non-NEUTRAL
    # branch — the schema (app/schemas/asset.py's TrendDirection) only
    # accepts "UP"/"DOWN"/"NEUTRAL", not "RISING"/"FALLING".
    await insert_funding(db_session, "TESTUSDT", 0.0001, 150.0, 1_700_800_000)
    await insert_funding(db_session, "TESTUSDT", 0.0003, 150.0, 1_700_900_000)

    derivatives = await get_derivatives_snapshot(db_session, "TEST")

    assert derivatives.funding_trend in ("UP", "DOWN", "NEUTRAL")
    assert derivatives.funding_trend == "UP"


@pytest.mark.asyncio
async def test_get_whales_snapshot_with_no_events(db_session):
    whales = await get_whales_snapshot(db_session, "TEST")

    assert whales.events == []
    assert whales.asset is None
    assert whales.to_exchange_usd_24h == 0.0


@pytest.mark.asyncio
async def test_get_whales_snapshot_with_events(db_session):
    await insert_whale_event(
        db_session,
        asset="ETH",
        amount=100.0,
        usd_value=250_000.0,
        wallet_type="EXCHANGE",
        direction="TO_EXCHANGE",
        exchange="Binance",
        confidence=90.0,
        from_address="0xabc",
        to_address="0xdef",
        tx_hash="0x123",
        timestamp=int(time.time()) - 3600,  # within get_whale_snapshot_for_symbol's lookback window
    )

    whales = await get_whales_snapshot(db_session, "ETH")

    assert len(whales.events) == 1
    assert whales.asset == "ETH"


@pytest.mark.asyncio
async def test_get_news_snapshot_filters_by_symbol(db_session):
    await insert_article(
        db_session,
        source="Test",
        title="ETH rallies",
        summary="summary",
        url="https://example.com/eth",
        published_at=1_700_900_000,
        language="en",
        symbols=["ETH"],
        impact_score=50.0,
        sentiment="BULLISH",
        category="Market",
    )
    await insert_article(
        db_session,
        source="Test",
        title="BTC dips",
        summary="summary",
        url="https://example.com/btc",
        published_at=1_700_900_000,
        language="en",
        symbols=["BTC"],
        impact_score=50.0,
        sentiment="BEARISH",
        category="Market",
    )

    articles = await get_news_snapshot(db_session, "ETH")

    assert len(articles) == 1
    assert articles[0].title == "ETH rallies"


@pytest.mark.asyncio
async def test_get_macro_snapshot_returns_a_reading_per_indicator(db_session):
    from app.intelligence.macro.symbols import MACRO_INDICATORS

    readings = await get_macro_snapshot(db_session)

    assert len(readings) == len(MACRO_INDICATORS)
    assert all(r.trend in ("UP", "DOWN", "NEUTRAL") for r in readings)
    assert all(r.influence in ("HIGH", "LOW") for r in readings)


@pytest.mark.asyncio
async def test_get_sentiment_snapshot_returns_none_without_candles(db_session):
    sentiment = await get_sentiment_snapshot(db_session, "NOPE")
    assert sentiment is None


@pytest.mark.asyncio
async def test_get_sentiment_snapshot_radar_matches_breakdown(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    sentiment = await get_sentiment_snapshot(db_session, "TEST")

    assert sentiment is not None
    assert sentiment.radar.social is None
    assert sentiment.radar.news == sentiment.result.breakdown["news"].score
    assert sentiment.radar.whale == sentiment.result.breakdown["whales"].score
    assert sentiment.radar.market_score == sentiment.result.overall_score
