"""Static Binance-symbol -> CoinGecko coin-id mapping.

CoinGecko has no concept of a trading pair; every coin has one canonical
id and every price is quoted directly against `vs_currency`. We use USD
as the practical stand-in for USDT here (spot BTC/USD and BTC/USDT track
within basis points of each other) — this is a fallback path, not a
precision instrument.

Extend this table when adding a new coin to `SYMBOLS` in `.env` if you
want the CoinGecko fallback to cover it too; an unmapped symbol simply
gets no fallback data (Binance-only), which is safe and non-fatal.
"""

SYMBOL_TO_COINGECKO_ID: dict[str, str] = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "LINKUSDT": "chainlink",
    "DOGEUSDT": "dogecoin",
    "BNBUSDT": "binancecoin",
    "XRPUSDT": "ripple",
}


def coingecko_id_for_symbol(symbol: str) -> str | None:
    return SYMBOL_TO_COINGECKO_ID.get(symbol.upper())
