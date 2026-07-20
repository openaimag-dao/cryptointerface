"""Builds Binance USDT-M Futures combined-stream names/URLs.

Stream reference: https://binance-docs.github.io/apidocs/futures/en/#websocket-market-streams
"""

from app.core.config import get_settings

settings = get_settings()

MAX_STREAMS_PER_CONNECTION = 200  # Binance allows up to 1024; we stay well under it.


def kline_stream(symbol: str, timeframe: str) -> str:
    return f"{symbol.lower()}@kline_{timeframe}"


def mini_ticker_stream(symbol: str) -> str:
    return f"{symbol.lower()}@miniTicker"


def mark_price_stream(symbol: str) -> str:
    return f"{symbol.lower()}@markPrice@1s"


def agg_trade_stream(symbol: str) -> str:
    return f"{symbol.lower()}@aggTrade"


def build_streams(symbols: list[str], timeframes: list[str]) -> list[str]:
    streams: list[str] = []
    for symbol in symbols:
        streams.append(mini_ticker_stream(symbol))
        streams.append(mark_price_stream(symbol))
        streams.append(agg_trade_stream(symbol))
        for timeframe in timeframes:
            streams.append(kline_stream(symbol, timeframe))
    return streams


def chunk_streams(streams: list[str], chunk_size: int = MAX_STREAMS_PER_CONNECTION) -> list[list[str]]:
    """Binance combined-stream URLs are long but the practical/documented
    cap is 1024 streams per connection; we chunk conservatively so a single
    connection drop only affects a subset of symbols."""
    return [streams[i : i + chunk_size] for i in range(0, len(streams), chunk_size)]


def build_combined_stream_url(streams: list[str], base_url: str | None = None) -> str:
    base = base_url or settings.binance_ws_base_url
    return f"{base}/stream?streams=" + "/".join(streams)
