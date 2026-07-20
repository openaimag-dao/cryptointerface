from typing import Literal

from pydantic import BaseModel

Direction = Literal["LONG", "SHORT", "WAIT"]
Sentiment = Literal["BULLISH", "BEARISH", "NEUTRAL"]


class Candle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class AssetQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change_percent_24h: float
    volume_24h: float
    funding_rate: float
    open_interest: float
    ai_score: int
    direction: Direction


class MarketOverview(BaseModel):
    fear_greed_index: int
    fear_greed_label: str
    btc_dominance: float
    avg_funding_rate: float
    total_open_interest: float
    total_volume_24h: float
