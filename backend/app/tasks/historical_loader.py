"""One-time (idempotent) backfill of historical candles on startup.

For each configured symbol/timeframe, tops up local storage to
`settings.historical_candles_per_timeframe` candles. Already-backfilled
pairs are skipped on restart, so this is safe to run every time the app
boots.
"""

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.binance.rest_client import BinanceRestClient
from app.services.market_repository import bulk_upsert_candles, count_candles, upsert_symbol

logger = get_logger(__name__)
settings = get_settings()

SessionFactory = Callable[[], AsyncSession]


def _split_asset(symbol: str) -> tuple[str, str]:
    for quote in ("USDT", "BUSD", "USDC"):
        if symbol.endswith(quote):
            return symbol[: -len(quote)], quote
    return symbol, ""


async def register_symbols(rest_client: BinanceRestClient, session_factory: SessionFactory, symbols: list[str]) -> None:
    by_symbol: dict[str, dict] = {}
    try:
        info = await rest_client.get_exchange_info()
        by_symbol = {entry["symbol"]: entry for entry in info.get("symbols", [])}
    except Exception as exc:  # noqa: BLE001 — metadata is best-effort, backfill must still proceed
        logger.warning("exchange_info_fetch_failed", extra={"error": str(exc)})

    async with session_factory() as db:
        for symbol in symbols:
            meta = by_symbol.get(symbol)
            if meta:
                await upsert_symbol(db, symbol, meta["baseAsset"], meta["quoteAsset"])
            else:
                base, quote = _split_asset(symbol)
                await upsert_symbol(db, symbol, base, quote)


async def backfill_symbol_timeframe(
    rest_client: BinanceRestClient,
    session_factory: SessionFactory,
    symbol: str,
    interval: str,
    target_count: int,
) -> None:
    async with session_factory() as db:
        existing = await count_candles(db, symbol, interval)

    if existing >= target_count:
        logger.info(
            "historical_backfill_skipped",
            extra={"symbol": symbol, "interval": interval, "existing": existing, "target": target_count},
        )
        return

    logger.info(
        "historical_backfill_starting",
        extra={"symbol": symbol, "interval": interval, "existing": existing, "target": target_count},
    )
    klines = await rest_client.fetch_historical_klines(symbol, interval, target_count)

    async with session_factory() as db:
        await bulk_upsert_candles(db, symbol, interval, klines)

    logger.info(
        "historical_backfill_completed",
        extra={"symbol": symbol, "interval": interval, "fetched": len(klines)},
    )


async def run_historical_backfill(
    session_factory: SessionFactory,
    symbols: list[str] | None = None,
    timeframes: list[str] | None = None,
    target_count: int | None = None,
) -> None:
    symbols = symbols or settings.symbol_list
    timeframes = timeframes or settings.timeframe_list
    target_count = target_count or settings.historical_candles_per_timeframe

    async with BinanceRestClient() as rest_client:
        await register_symbols(rest_client, session_factory, symbols)

        for symbol in symbols:
            for interval in timeframes:
                try:
                    await backfill_symbol_timeframe(rest_client, session_factory, symbol, interval, target_count)
                except Exception as exc:  # noqa: BLE001 — one bad pair must not abort the whole backfill
                    logger.error(
                        "historical_backfill_failed",
                        extra={"symbol": symbol, "interval": interval, "error": str(exc)},
                    )

    logger.info("historical_backfill_all_done", extra={"symbols": symbols, "timeframes": timeframes})
