"""Fetches every registered macro indicator and persists each reading.

Called by the scheduler (`app/intelligence/scheduler/tasks.py`) on
`MACRO_POLL_INTERVAL_SECONDS`. One indicator failing (rate limit, no API
key, transient network error) never blocks the others — each fetch is
independently try/except'd inside the provider functions themselves (see
`providers.py`), so this function always runs to completion.
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.intelligence.macro.providers import AlphaVantageClient, fetch_fear_greed_index
from app.intelligence.macro.symbols import MACRO_INDICATORS
from app.services.coingecko.client import CoinGeckoRestClient
from app.services.macro_repository import insert_macro_point

logger = get_logger(__name__)


async def fetch_and_persist_macro_snapshot(db: AsyncSession) -> dict[str, float | None]:
    """Fetches every indicator in `MACRO_INDICATORS` once and persists
    whichever ones returned a value. Returns {indicator_id: value|None}
    for logging/testing."""
    results: dict[str, float | None] = {}
    fetched_at = int(datetime.now(UTC).timestamp())

    av_client = AlphaVantageClient()
    coingecko_client = CoinGeckoRestClient()
    try:
        for indicator in MACRO_INDICATORS:
            value: float | None = None
            try:
                if indicator.provider == "alpha_vantage_etf":
                    assert indicator.av_ticker is not None
                    value = await av_client.get_etf_daily_close(indicator.av_ticker)
                elif indicator.provider == "alpha_vantage_treasury":
                    value = await av_client.get_treasury_yield()
                elif indicator.provider == "fear_greed":
                    value = await fetch_fear_greed_index()
                elif indicator.provider == "coingecko_global":
                    value = await coingecko_client.get_global_data()
                else:
                    logger.warning("unknown_macro_provider", extra={"indicator": indicator.id})
            except Exception:
                logger.warning("macro_indicator_fetch_failed", extra={"indicator": indicator.id}, exc_info=True)
                value = None

            results[indicator.id] = value
            if value is not None:
                await insert_macro_point(
                    db, indicator=indicator.id, value=value, source=indicator.provider, fetched_at=fetched_at
                )
    finally:
        await av_client.close()
        await coingecko_client.close()

    fetched_count = sum(1 for v in results.values() if v is not None)
    logger.info("macro_snapshot_fetched", extra={"fetched": fetched_count, "total": len(results)})
    return results
