"""One-time (idempotent) backfill of historical candles on startup.

For each configured symbol/timeframe, tops up local storage to
`settings.historical_candles_per_timeframe` candles. Already-backfilled
pairs are skipped on restart, so this is safe to run every time the app
boots.

If Binance is unreachable (e.g. geo-restricted egress), `1h`/`4h` candles
fall back to CoinGecko's public OHLC endpoint on a best-effort basis — see
`app/services/coingecko/candles.py` for exactly what that covers and its
limitations (no volume, coarser/approximate granularity, no 1m/5m/15m/1d
support). Binance stays the primary source; this only activates per
symbol/interval when Binance's own retries are already exhausted.
"""

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.binance.rest_client import BinanceRestClient, KlineData
from app.services.coingecko.candles import fetch_coingecko_fallback_klines, is_supported
from app.services.coingecko.client import CoinGeckoRestClient
from app.services.coingecko.symbols import coingecko_id_for_symbol
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


async def _coingecko_fallback(
    coingecko_client: CoinGeckoRestClient | None, symbol: str, interval: str, binance_error: Exception
) -> list[KlineData] | None:
    if coingecko_client is None or not is_supported(interval):
        return None
    coin_id = coingecko_id_for_symbol(symbol)
    if coin_id is None:
        return None

    logger.warning(
        "binance_backfill_failed_trying_coingecko",
        extra={"symbol": symbol, "interval": interval, "binance_error": str(binance_error)},
    )
    try:
        klines = await fetch_coingecko_fallback_klines(coingecko_client, coin_id, interval)
    except Exception as exc:  # noqa: BLE001 — fallback is best-effort, must not crash the loader
        logger.warning("coingecko_fallback_failed", extra={"symbol": symbol, "interval": interval, "error": str(exc)})
        return None

    return klines or None


async def backfill_symbol_timeframe(
    rest_client: BinanceRestClient,
    session_factory: SessionFactory,
    symbol: str,
    interval: str,
    target_count: int,
    coingecko_client: CoinGeckoRestClient | None = None,
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

    source = "binance"
    try:
        klines = await rest_client.fetch_historical_klines(symbol, interval, target_count)
    except Exception as exc:
        fallback_klines = await _coingecko_fallback(coingecko_client, symbol, interval, exc)
        if fallback_klines is None:
            raise
        klines = fallback_klines
        source = "coingecko_fallback"

    async with session_factory() as db:
        await bulk_upsert_candles(db, symbol, interval, klines)

    logger.info(
        "historical_backfill_completed",
        extra={"symbol": symbol, "interval": interval, "fetched": len(klines), "source": source},
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

    async with BinanceRestClient() as rest_client, CoinGeckoRestClient() as coingecko_client:
        await register_symbols(rest_client, session_factory, symbols)

        for symbol in symbols:
            for interval in timeframes:
                try:
                    await backfill_symbol_timeframe(
                        rest_client, session_factory, symbol, interval, target_count, coingecko_client
                    )
                except Exception as exc:  # noqa: BLE001 — one bad pair must not abort the whole backfill
                    logger.error(
                        "historical_backfill_failed",
                        extra={"symbol": symbol, "interval": interval, "error": str(exc)},
                    )

    logger.info("historical_backfill_all_done", extra={"symbols": symbols, "timeframes": timeframes})
