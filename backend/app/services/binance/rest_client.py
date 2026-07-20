"""Async REST client for Binance USDT-M Futures public market data.

Deliberately only wraps *public* endpoints (klines, 24hr ticker, funding
rate / mark price, open interest, exchange info) — no signed/account
endpoints. `BINANCE_API_KEY`/`SECRET` in config are reserved for Sprint 3+
private trading endpoints and are not read here.
"""

import asyncio
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.retry import retry_async

logger = get_logger(__name__)
settings = get_settings()

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class BinanceRestError(Exception):
    pass


@dataclass(frozen=True)
class KlineData:
    open_time: int  # unix ms
    close_time: int  # unix ms
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trades: int


def _parse_kline(raw: list) -> KlineData:
    return KlineData(
        open_time=int(raw[0]),
        open=float(raw[1]),
        high=float(raw[2]),
        low=float(raw[3]),
        close=float(raw[4]),
        volume=float(raw[5]),
        close_time=int(raw[6]),
        quote_volume=float(raw[7]),
        trades=int(raw[8]),
    )


class BinanceRestClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self._base_url = base_url or settings.binance_rest_base_url
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BinanceRestClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        async def _do_request() -> dict | list:
            response = await self._client.get(path, params=params)
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise BinanceRestError(f"Retryable status {response.status_code} from {path}: {response.text[:200]}")
            if response.is_error:
                raise BinanceRestError(f"Binance REST error {response.status_code} from {path}: {response.text[:200]}")
            return response.json()

        return await retry_async(
            _do_request,
            max_attempts=4,
            base_delay=0.5,
            max_delay=10.0,
            retry_exceptions=(BinanceRestError, httpx.TransportError, httpx.TimeoutException),
        )

    async def ping(self) -> bool:
        try:
            await self._get("/fapi/v1/ping")
            return True
        except Exception as exc:  # noqa: BLE001 — health check, never raises
            logger.warning("binance_ping_failed", extra={"error": str(exc)})
            return False

    async def get_exchange_info(self) -> dict:
        result = await self._get("/fapi/v1/exchangeInfo")
        assert isinstance(result, dict)
        return result

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 1500,
        end_time_ms: int | None = None,
        start_time_ms: int | None = None,
    ) -> list[KlineData]:
        params: dict[str, str | int] = {"symbol": symbol, "interval": interval, "limit": min(limit, 1500)}
        if end_time_ms is not None:
            params["endTime"] = end_time_ms
        if start_time_ms is not None:
            params["startTime"] = start_time_ms

        raw = await self._get("/fapi/v1/klines", params=params)
        assert isinstance(raw, list)
        return [_parse_kline(row) for row in raw]

    async def fetch_historical_klines(self, symbol: str, interval: str, total: int) -> list[KlineData]:
        """Backfill up to `total` most-recent closed candles, oldest-first."""
        collected: list[KlineData] = []
        end_time_ms: int | None = None

        while len(collected) < total:
            batch = await self.get_klines(symbol, interval, limit=1500, end_time_ms=end_time_ms)
            if not batch:
                break

            collected = batch + collected
            end_time_ms = batch[0].open_time - 1

            # Be a good citizen between paginated requests.
            await asyncio.sleep(0.2)

        # Drop the last (potentially still-open) candle and trim to `total`.
        if collected:
            collected = collected[:-1] if len(collected) > total else collected
        return collected[-total:]

    async def get_ticker_24hr(self, symbol: str) -> dict:
        result = await self._get("/fapi/v1/ticker/24hr", params={"symbol": symbol})
        assert isinstance(result, dict)
        return result

    async def get_all_tickers_24hr(self) -> list[dict]:
        result = await self._get("/fapi/v1/ticker/24hr")
        assert isinstance(result, list)
        return result

    async def get_premium_index(self, symbol: str) -> dict:
        result = await self._get("/fapi/v1/premiumIndex", params={"symbol": symbol})
        assert isinstance(result, dict)
        return result

    async def get_open_interest(self, symbol: str) -> dict:
        result = await self._get("/fapi/v1/openInterest", params={"symbol": symbol})
        assert isinstance(result, dict)
        return result
