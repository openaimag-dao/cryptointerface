"""Periodic REST poller for open interest.

Binance does not publish open interest over WebSocket — `/fapi/v1/openInterest`
is REST-only — so this task polls it on an interval instead of reacting to
a stream event like the rest of the live feed.
"""

import asyncio
import time

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.redis import FUNDING_KEY, OPEN_INTEREST_KEY, cache_get_json, cache_set_json
from app.database.session import AsyncSessionLocal
from app.services.binance.rest_client import BinanceRestClient
from app.services.market_repository import insert_open_interest

logger = get_logger(__name__)
settings = get_settings()

DEFAULT_POLL_INTERVAL_SECONDS = 60.0


async def poll_open_interest_once(rest_client: BinanceRestClient, symbols: list[str]) -> None:
    for symbol in symbols:
        try:
            data = await rest_client.get_open_interest(symbol)
        except Exception as exc:  # noqa: BLE001 — one symbol failing must not stop the others
            logger.warning("open_interest_poll_failed", extra={"symbol": symbol, "error": str(exc)})
            continue

        open_interest = float(data["openInterest"])
        try:
            mark_price_payload = await cache_get_json(FUNDING_KEY.format(symbol=symbol))
        except Exception:  # noqa: BLE001 — best-effort enrichment only
            mark_price_payload = None

        mark_price = mark_price_payload["mark_price"] if mark_price_payload else None
        open_interest_value = open_interest * mark_price if mark_price else 0.0
        timestamp = int(data.get("time", time.time() * 1000))

        payload = {
            "symbol": symbol,
            "open_interest": open_interest,
            "open_interest_value": open_interest_value,
            "timestamp": timestamp,
        }
        await cache_set_json(OPEN_INTEREST_KEY.format(symbol=symbol), payload)

        async with AsyncSessionLocal() as db:
            await insert_open_interest(db, symbol, open_interest, open_interest_value, timestamp)


async def run_open_interest_poller(
    symbols: list[str] | None = None,
    interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    stop_event: asyncio.Event | None = None,
) -> None:
    symbols = symbols or settings.symbol_list
    stop_event = stop_event or asyncio.Event()

    async with BinanceRestClient() as rest_client:
        while not stop_event.is_set():
            await poll_open_interest_once(rest_client, symbols)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                pass  # normal: just means it's time to poll again
