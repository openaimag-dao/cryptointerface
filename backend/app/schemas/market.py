from typing import Literal

from app.schemas.base import CamelModel

Direction = Literal["LONG", "SHORT", "WAIT"]
Sentiment = Literal["BULLISH", "BEARISH", "NEUTRAL"]


class MarketAsset(CamelModel):
    """Real-time snapshot for a single symbol, sourced from Binance."""

    symbol: str
    price: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    quote_volume_24h: float
    funding_rate: float | None = None
    open_interest: float | None = None
    updated_at: str


class TickerUpdate(CamelModel):
    """24h ticker tick, pushed over WebSocket on the "ticker" channel."""

    symbol: str
    price: float
    change_percent_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    quote_volume_24h: float
