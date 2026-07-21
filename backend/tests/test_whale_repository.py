from datetime import UTC, datetime

import pytest

from app.services.whale_repository import (
    get_recent_whale_events,
    get_whale_snapshot_for_symbol,
    insert_whale_event,
)


async def _insert(
    db_session,
    *,
    tx_hash: str,
    asset: str = "ETH",
    direction: str = "TO_EXCHANGE",
    usd_value: float = 500_000.0,
    timestamp: int | None = None,
):
    return await insert_whale_event(
        db_session,
        asset=asset,
        amount=100.0,
        usd_value=usd_value,
        wallet_type="EXCHANGE",
        direction=direction,
        exchange="Binance",
        confidence=90.0,
        from_address="0xfrom",
        to_address="0xto",
        tx_hash=tx_hash,
        timestamp=timestamp if timestamp is not None else int(datetime.now(UTC).timestamp()),
    )


@pytest.mark.asyncio
async def test_insert_whale_event_dedupes_on_tx_hash(db_session):
    first = await _insert(db_session, tx_hash="0xhash1")
    second = await _insert(db_session, tx_hash="0xhash1")

    assert first is True
    assert second is False

    events = await get_recent_whale_events(db_session, limit=10)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_get_recent_whale_events_filters_by_asset(db_session):
    await _insert(db_session, tx_hash="0xeth", asset="ETH")
    await _insert(db_session, tx_hash="0xlink", asset="LINK")

    eth_only = await get_recent_whale_events(db_session, limit=10, asset="ETH")

    assert len(eth_only) == 1
    assert eth_only[0].asset == "ETH"


@pytest.mark.asyncio
async def test_get_whale_snapshot_for_symbol_none_for_unmapped_symbol(db_session):
    snapshot = await get_whale_snapshot_for_symbol(db_session, "BTCUSDT")
    assert snapshot is None


@pytest.mark.asyncio
async def test_get_whale_snapshot_for_symbol_none_without_events(db_session):
    snapshot = await get_whale_snapshot_for_symbol(db_session, "ETHUSDT")
    assert snapshot is None


@pytest.mark.asyncio
async def test_get_whale_snapshot_for_symbol_sums_by_direction(db_session):
    await _insert(db_session, tx_hash="0xa", asset="ETH", direction="TO_EXCHANGE", usd_value=300_000.0)
    await _insert(db_session, tx_hash="0xb", asset="ETH", direction="FROM_EXCHANGE", usd_value=500_000.0)

    snapshot = await get_whale_snapshot_for_symbol(db_session, "ETHUSDT")

    assert snapshot is not None
    assert snapshot.event_count == 2
    assert snapshot.to_exchange_usd == 300_000.0
    assert snapshot.from_exchange_usd == 500_000.0


@pytest.mark.asyncio
async def test_get_whale_snapshot_for_symbol_excludes_events_outside_24h_window(db_session):
    stale_timestamp = int(datetime.now(UTC).timestamp()) - (25 * 3600)
    await _insert(db_session, tx_hash="0xstale", asset="ETH", timestamp=stale_timestamp)

    snapshot = await get_whale_snapshot_for_symbol(db_session, "ETHUSDT")

    assert snapshot is None
