"""Async REST client for CoinGecko's free public API.

Used only as a fallback when Binance is unreachable (e.g. geo-restricted
egress — see `app/services/binance/rest_client.py`'s docstring for the
primary source). Spot market data only: no funding rate, no open
interest, no WebSocket. Those stay Binance-only and simply have no data
while this fallback is active — the AI engine's funding/oi scoring
modules already degrade gracefully to a neutral read when there's no
history (see `app/ai_engine/scoring/funding.py`, `oi.py`).
"""

from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.retry import retry_async

logger = get_logger(__name__)
settings = get_settings()

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class CoinGeckoRestError(Exception):
    pass


@dataclass(frozen=True)
class MarketSnapshot:
    coin_id: str
    price: float
    high_24h: float
    low_24h: float
    change_percent_24h: float
    volume_24h: float
    # Only populated by get_markets() when `include_extended=True` (the
    # Asset Intelligence Dashboard's top bar, see app/services/asset_service.py) —
    # the Binance-fallback ticker poller doesn't need these and stays on
    # the cheaper default request shape.
    market_cap: float | None = None
    change_percent_7d: float | None = None
    change_percent_30d: float | None = None


@dataclass(frozen=True)
class OhlcCandle:
    open_time: int  # unix ms
    open: float
    high: float
    low: float
    close: float


class CoinGeckoRestClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self._base_url = base_url or settings.coingecko_base_url
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "CoinGeckoRestClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        async def _do_request() -> dict | list:
            response = await self._client.get(path, params=params)
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise CoinGeckoRestError(f"Retryable status {response.status_code} from {path}: {response.text[:200]}")
            if response.is_error:
                raise CoinGeckoRestError(
                    f"CoinGecko REST error {response.status_code} from {path}: {response.text[:200]}"
                )
            return response.json()

        return await retry_async(
            _do_request,
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0,
            retry_exceptions=(CoinGeckoRestError, httpx.TransportError, httpx.TimeoutException),
        )

    async def ping(self) -> bool:
        try:
            await self._get("/ping")
            return True
        except Exception as exc:  # noqa: BLE001 — health check, never raises
            logger.warning("coingecko_ping_failed", extra={"error": str(exc)})
            return False

    async def get_markets(self, coin_ids: list[str], include_extended: bool = False) -> dict[str, MarketSnapshot]:
        """One REST call, current price + 24h stats for every requested coin.
        `include_extended=True` also requests market cap and 7d/30d change —
        the Binance-fallback ticker poller doesn't need those, only the
        Asset Intelligence Dashboard's top bar does (see `asset_service.py`)."""
        if not coin_ids:
            return {}

        change_windows = "24h,7d,30d" if include_extended else "24h"
        raw = await self._get(
            "/coins/markets",
            params={"vs_currency": "usd", "ids": ",".join(coin_ids), "price_change_percentage": change_windows},
        )
        assert isinstance(raw, list)

        result: dict[str, MarketSnapshot] = {}
        for row in raw:
            coin_id = row.get("id")
            price = row.get("current_price")
            if coin_id is None or price is None:
                continue
            market_cap = row.get("market_cap")
            change_7d = row.get("price_change_percentage_7d_in_currency")
            change_30d = row.get("price_change_percentage_30d_in_currency")
            result[coin_id] = MarketSnapshot(
                coin_id=coin_id,
                price=float(price),
                high_24h=float(row.get("high_24h") or price),
                low_24h=float(row.get("low_24h") or price),
                change_percent_24h=float(row.get("price_change_percentage_24h") or 0.0),
                volume_24h=float(row.get("total_volume") or 0.0),
                market_cap=float(market_cap) if market_cap is not None else None,
                change_percent_7d=float(change_7d) if change_7d is not None else None,
                change_percent_30d=float(change_30d) if change_30d is not None else None,
            )
        return result

    async def get_global_data(self) -> float | None:
        """BTC's share of total crypto market cap (0-100), used by the
        Macro Engine (`app/intelligence/macro/`) — unrelated to the
        Binance-fallback role of the rest of this client, but the same
        free/keyless endpoint family so it lives here rather than a
        second client."""
        raw = await self._get("/global")
        assert isinstance(raw, dict)
        btc_pct = raw.get("data", {}).get("market_cap_percentage", {}).get("btc")
        return float(btc_pct) if btc_pct is not None else None

    async def get_ohlc(self, coin_id: str, days: int) -> list[OhlcCandle]:
        """Free-tier granularity is fixed by `days`, not independently
        selectable: 1-2 days -> 30min bars, 3-30 days -> 4h bars,
        31+ days -> 4-day bars. Callers pick `days` to hit the granularity
        they want (see `app/services/coingecko/candles.py`)."""
        raw = await self._get(f"/coins/{coin_id}/ohlc", params={"vs_currency": "usd", "days": days})
        assert isinstance(raw, list)
        return [
            OhlcCandle(
                open_time=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
            )
            for row in raw
        ]
