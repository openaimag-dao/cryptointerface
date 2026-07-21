"""Best-effort candle fallback via CoinGecko OHLC.

Only two intervals are supported: `4h` (native 4h granularity on the free
tier) and `1h` (approximated by resampling CoinGecko's 30min bars to
every other bar so timestamps land roughly an hour apart). `1m`/`5m`/`15m`
have no matching CoinGecko granularity on the free API, and there's no
clean 1-day granularity either — those intervals simply get no fallback
data and stay empty until Binance is reachable again.
"""

from app.services.binance.rest_client import KlineData
from app.services.coingecko.client import CoinGeckoRestClient, OhlcCandle

# interval -> `days` param that yields that granularity on CoinGecko's
# free OHLC endpoint (1-2 days -> 30min bars, 3-30 days -> 4h bars).
_SUPPORTED_INTERVAL_DAYS: dict[str, int] = {
    "1h": 1,
    "4h": 30,
}
_INTERVAL_MS: dict[str, int] = {"1h": 3_600_000, "4h": 14_400_000}


def is_supported(interval: str) -> bool:
    return interval in _SUPPORTED_INTERVAL_DAYS


def _to_kline(candle: OhlcCandle, interval_ms: int) -> KlineData:
    return KlineData(
        open_time=candle.open_time,
        close_time=candle.open_time + interval_ms - 1,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=0.0,  # CoinGecko's free OHLC endpoint doesn't return volume
        quote_volume=0.0,
        trades=0,
    )


async def fetch_coingecko_fallback_klines(client: CoinGeckoRestClient, coin_id: str, interval: str) -> list[KlineData]:
    days = _SUPPORTED_INTERVAL_DAYS.get(interval)
    if days is None:
        return []

    raw = await client.get_ohlc(coin_id, days)

    if interval == "1h":
        # `days=1` gives 30min bars; keep every other one so timestamps
        # land ~1h apart. Each bar's OHLC still only reflects its native
        # 30min slice, not the full hour — an accepted approximation for
        # a fallback path, not a precision source.
        raw = raw[::2]

    interval_ms = _INTERVAL_MS[interval]
    return [_to_kline(candle, interval_ms) for candle in raw]
