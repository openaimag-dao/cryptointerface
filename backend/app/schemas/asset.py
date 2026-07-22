"""Asset Intelligence Dashboard schemas (Sprint 8 spec) — one per-symbol
research terminal tab. See `app/services/asset_service.py` for how each
is assembled from the existing Data/AI/Intelligence Engines.
"""

from typing import Literal

from app.schemas.base import CamelModel
from app.schemas.market import Direction
from app.schemas.sentiment import SentimentCategory
from app.schemas.whale import WhaleTransaction

IndicatorStatus = Literal[
    "BULLISH",
    "BEARISH",
    "NEUTRAL",
    "OVERBOUGHT",
    "OVERSOLD",
    "TRENDING",
    "RANGING",
    "TRANSITIONAL",
    "HIGH",
    "LOW",
    "MODERATE",
]
SmartMoneyStatus = Literal["BULLISH", "BEARISH", "NEUTRAL", "NOT_YET_IMPLEMENTED"]
BreakoutStatus = Literal["BROKEN_ABOVE_RESISTANCE", "BROKEN_BELOW_SUPPORT", "INSIDE_RANGE"]
TrendDirection = Literal["UP", "DOWN", "NEUTRAL"]
MacroInfluence = Literal["HIGH", "LOW"]


class AssetSummaryOut(CamelModel):
    """The top bar — shown on every tab."""

    symbol: str
    base_asset: str
    price: float
    change_percent_24h: float
    change_percent_7d: float | None
    change_percent_30d: float | None
    market_cap: float | None
    volume_24h: float
    funding_rate: float | None
    open_interest: float | None
    market_score: float | None
    confidence: float | None
    direction: Direction | None


class IndicatorReadingOut(CamelModel):
    name: str
    value: str
    status: IndicatorStatus
    explanation: str


class AssetOverviewOut(CamelModel):
    trend_status: Direction
    volatility_status: Direction
    atr: IndicatorReadingOut
    rsi: IndicatorReadingOut
    macd: IndicatorReadingOut
    ema_alignment: IndicatorReadingOut
    vwap: IndicatorReadingOut


class SmartMoneyConceptOut(CamelModel):
    name: str
    status: SmartMoneyStatus
    value: str | None
    explanation: str


class AssetTechnicalOut(CamelModel):
    symbol: str
    interval: str
    indicators: list[IndicatorReadingOut]
    smart_money: list[SmartMoneyConceptOut]
    nearest_support: float | None
    nearest_resistance: float | None
    breakout_status: BreakoutStatus


class FundingHistoryPointOut(CamelModel):
    time: int
    rate: float


class LiquidationClusterOut(CamelModel):
    price_low: float
    price_high: float
    total_usd: float
    event_count: int


class AssetDerivativesOut(CamelModel):
    symbol: str
    funding_rate: float | None
    funding_history: list[FundingHistoryPointOut]
    funding_trend: TrendDirection
    open_interest: float | None
    open_interest_value: float | None
    oi_delta_percent: float | None
    liquidation_clusters: list[LiquidationClusterOut]


class MacroInfluenceReadingOut(CamelModel):
    id: str
    label: str
    current: float | None
    change_percent: float | None
    trend: TrendDirection
    influence: MacroInfluence


class SentimentRadarOut(CamelModel):
    news: float
    social: float | None
    whale: float
    technical: float
    macro: float
    market_score: float


class AssetWhalesOut(CamelModel):
    symbol: str
    asset: str | None
    whale_score: float
    events: list[WhaleTransaction]
    to_exchange_usd_24h: float
    from_exchange_usd_24h: float


class AssetSentimentOut(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    overall_score: float
    confidence: float
    direction: Direction
    breakdown: dict[str, SentimentCategory]
    reasons: list[str]
    radar: SentimentRadarOut
