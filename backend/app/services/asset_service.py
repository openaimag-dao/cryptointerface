"""Asset Intelligence Dashboard aggregation layer (Sprint 8 spec).

Every function here wraps *existing* engines/repositories per symbol —
nothing in this module recomputes anything the Data/AI/Intelligence
Engines already own. It exists purely to assemble their outputs into the
shapes `/api/assets/{symbol}/*` needs, the same "aggregation, not new
computation" role `app/api/dashboard_intelligence.py` plays for the
Dashboard's Intelligence Card.

URLs use the bare asset (`/assets/BTC`); the Data Engine's tables key off
the USDT trading pair (`BTCUSDT`). `to_trading_pair`/`to_base_asset`
convert between them — every quote asset in this app is USDT (see
`app/core/config.py`'s `DEFAULT_SYMBOLS`), so a simple suffix is
sufficient; there is no per-symbol lookup table to keep in sync.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import AIDecision, analyze_market
from app.ai_engine.indicator_explain import IndicatorReading, explain_indicators, liquidity_score_reading
from app.ai_engine.market_context import build_market_context
from app.ai_engine.risk_analysis import RiskAnalysis, analyze_risk
from app.ai_engine.scenario_analysis import Scenario, analyze_scenarios
from app.ai_engine.scoring.whales import score_whales
from app.ai_engine.smart_money import SmartMoneyConcept, analyze_smart_money
from app.intelligence.macro.symbols import MACRO_INDICATORS
from app.intelligence.sentiment.engine import SentimentResult, compute_sentiment
from app.models.news import NewsArticle
from app.models.whale import WhaleEvent
from app.schemas.indicator import IndicatorSnapshot
from app.services.coingecko.client import CoinGeckoRestClient, MarketSnapshot
from app.services.coingecko.symbols import coingecko_id_for_symbol
from app.services.correlation_service import CorrelationReading, compute_correlations
from app.services.history_service import HISTORY_LIMIT, HistorySummary, get_history_summary
from app.services.timeline_service import TIMELINE_LIMIT, TimelineSummary, get_timeline
from app.services.indicators.engine import compute_indicators
from app.services.macro_repository import get_latest_points
from app.services.market_repository import (
    get_latest_funding,
    get_latest_open_interest,
    get_market_stat,
    get_recent_funding_history,
    get_recent_liquidations,
    get_recent_open_interest_history,
)
from app.services.news_repository import get_latest_news
from app.services.whale_repository import get_recent_whale_events, get_whale_snapshot_for_symbol

QUOTE_ASSET = "USDT"


def to_trading_pair(base_asset: str) -> str:
    return f"{base_asset.upper()}{QUOTE_ASSET}"


def to_base_asset(symbol: str) -> str:
    upper = symbol.upper()
    return upper[: -len(QUOTE_ASSET)] if upper.endswith(QUOTE_ASSET) else upper


# ---------------------------------------------------------------------------
# Overview / top bar
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssetSummary:
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
    direction: str | None


async def _fetch_extended_market_data(base_asset: str) -> MarketSnapshot | None:
    """Market cap / 7d / 30d change — Binance has no supply data at all,
    so this always goes to CoinGecko regardless of whether Binance is
    reachable for the primary ticker feed. Best-effort: an unmapped
    symbol or an unreachable CoinGecko simply means these fields are
    `None`, same fail-open tolerance as the rest of the app."""
    coin_id = coingecko_id_for_symbol(to_trading_pair(base_asset))
    if coin_id is None:
        return None
    try:
        async with CoinGeckoRestClient() as client:
            markets = await client.get_markets([coin_id], include_extended=True)
        return markets.get(coin_id)
    except Exception:  # noqa: BLE001 — best-effort enrichment, never fatal to the page
        return None


async def get_asset_summary(db: AsyncSession, base_asset: str, interval: str = "1h") -> AssetSummary | None:
    symbol = to_trading_pair(base_asset)
    stat = await get_market_stat(db, symbol)
    if stat is None:
        return None

    extended = await _fetch_extended_market_data(base_asset)
    funding = await get_latest_funding(db, symbol)
    open_interest = await get_latest_open_interest(db, symbol)

    ctx = await build_market_context(db, symbol, interval)
    decision: AIDecision | None = analyze_market(ctx) if ctx is not None else None

    return AssetSummary(
        symbol=symbol,
        base_asset=base_asset.upper(),
        price=stat.price,
        change_percent_24h=stat.change_percent_24h,
        change_percent_7d=extended.change_percent_7d if extended else None,
        change_percent_30d=extended.change_percent_30d if extended else None,
        market_cap=extended.market_cap if extended else None,
        volume_24h=stat.volume_24h,
        funding_rate=funding.funding_rate if funding else None,
        open_interest=open_interest.open_interest if open_interest else None,
        market_score=decision.market_score if decision else None,
        confidence=decision.confidence if decision else None,
        direction=decision.direction if decision else None,
    )


# ---------------------------------------------------------------------------
# Overview tab
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssetOverview:
    trend_status: str
    volatility_status: str
    atr: IndicatorReading
    rsi: IndicatorReading
    macd: IndicatorReading
    ema_alignment: IndicatorReading
    vwap: IndicatorReading
    volume_trend: IndicatorReading
    liquidity_score: IndicatorReading


_OVERVIEW_INDICATOR_NAMES = {"ATR (14)", "RSI (14)", "MACD", "EMA Alignment", "VWAP"}


async def get_overview_snapshot(db: AsyncSession, base_asset: str, interval: str = "1h") -> AssetOverview | None:
    """The Overview tab's "Market Snapshot" panel — price/market cap/volume
    live in `AssetSummary` (the same top-bar data, not refetched here);
    this adds the handful of indicator reads specific to that panel
    (Trend, Volatility, ATR, RSI, MACD, EMA Alignment, VWAP)."""
    symbol = to_trading_pair(base_asset)
    ctx = await build_market_context(db, symbol, interval)
    if ctx is None:
        return None

    snapshot: IndicatorSnapshot = compute_indicators(symbol, interval, ctx.candles)
    by_name = {r.name: r for r in explain_indicators(snapshot, ctx.closes, ctx.volumes)}

    decision = analyze_market(ctx)
    trend_factor = decision.factors.get("trend")
    volatility_factor = decision.factors.get("volatility")

    # "Volume Trend" relabels the Technical tab's OBV read rather than
    # recomputing it, so the two panels never disagree.
    obv_reading = by_name.get("OBV")
    volume_trend = (
        IndicatorReading("Volume Trend", obv_reading.value, obv_reading.status, obv_reading.explanation)
        if obv_reading
        else IndicatorReading("Volume Trend", "—", "NEUTRAL", "Not enough history yet.")
    )

    return AssetOverview(
        trend_status=trend_factor.direction if trend_factor else "WAIT",
        volatility_status=volatility_factor.direction if volatility_factor else "WAIT",
        atr=by_name.get("ATR (14)") or IndicatorReading("ATR (14)", "—", "NEUTRAL", "Not enough history yet."),
        rsi=by_name.get("RSI (14)") or IndicatorReading("RSI (14)", "—", "NEUTRAL", "Not enough history yet."),
        macd=by_name.get("MACD") or IndicatorReading("MACD", "—", "NEUTRAL", "Not enough history yet."),
        ema_alignment=by_name.get("EMA Alignment")
        or IndicatorReading("EMA Alignment", "—", "NEUTRAL", "Not enough history yet."),
        vwap=by_name.get("VWAP") or IndicatorReading("VWAP", "—", "NEUTRAL", "Not enough history yet."),
        volume_trend=volume_trend,
        liquidity_score=liquidity_score_reading(ctx.closes, ctx.volumes),
    )


# ---------------------------------------------------------------------------
# Technical tab
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssetTechnical:
    symbol: str
    interval: str
    indicators: list[IndicatorReading]
    smart_money: list[SmartMoneyConcept]
    nearest_support: float | None
    nearest_resistance: float | None
    breakout_status: str


async def get_technical_snapshot(db: AsyncSession, base_asset: str, interval: str = "1h") -> AssetTechnical | None:
    symbol = to_trading_pair(base_asset)
    ctx = await build_market_context(db, symbol, interval)
    if ctx is None:
        return None

    snapshot: IndicatorSnapshot = compute_indicators(symbol, interval, ctx.candles)
    indicators = explain_indicators(snapshot, ctx.closes, ctx.volumes)
    smart_money = analyze_smart_money(ctx.closes, ctx.highs, ctx.lows, ctx.opens, ctx.volumes)

    decision = analyze_market(ctx)
    structure = decision.factors.get("structure")
    support = structure.details.get("nearest_support") if structure else None
    resistance = structure.details.get("nearest_resistance") if structure else None
    price = ctx.last_close
    if resistance is not None and isinstance(resistance, int | float) and price > resistance:
        breakout_status = "BROKEN_ABOVE_RESISTANCE"
    elif support is not None and isinstance(support, int | float) and price < support:
        breakout_status = "BROKEN_BELOW_SUPPORT"
    else:
        breakout_status = "INSIDE_RANGE"

    return AssetTechnical(
        symbol=symbol,
        interval=interval,
        indicators=indicators,
        smart_money=smart_money,
        nearest_support=support if isinstance(support, int | float) else None,
        nearest_resistance=resistance if isinstance(resistance, int | float) else None,
        breakout_status=breakout_status,
    )


# ---------------------------------------------------------------------------
# Derivatives tab
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LiquidationCluster:
    price_low: float
    price_high: float
    total_usd: float
    event_count: int


@dataclass(frozen=True)
class ExchangeBreakdown:
    exchange: str
    status: str  # "AVAILABLE" | "NOT_YET_IMPLEMENTED"
    open_interest: float | None
    funding_rate: float | None
    note: str


@dataclass(frozen=True)
class AssetDerivatives:
    symbol: str
    funding_rate: float | None
    funding_history: list[tuple[int, float]]  # (funding_time, rate)
    funding_trend: str
    open_interest: float | None
    open_interest_value: float | None
    oi_delta_percent: float | None
    liquidation_clusters: list[LiquidationCluster]
    exchange_breakdown: list[ExchangeBreakdown]


LIQUIDATION_CLUSTER_COUNT = 6
FUNDING_HISTORY_LIMIT = 20
OI_HISTORY_LIMIT = 20

# Architecture-only per the Sprint 6 spec: this app has exactly one real
# derivatives data source (Binance USDT-M Futures — see
# app/services/binance/rest_client.py's docstring for why it stays the
# only one). Adding another exchange means a new REST/WS client, not a
# UI change, so these report NOT_YET_IMPLEMENTED honestly rather than
# faking a number no client here has ever fetched.
_UNINTEGRATED_EXCHANGES = ("Bybit", "OKX", "Bitget")


def _exchange_breakdown(open_interest: float | None, funding_rate: float | None) -> list[ExchangeBreakdown]:
    entries = [
        ExchangeBreakdown(
            exchange="Binance",
            status="AVAILABLE",
            open_interest=open_interest,
            funding_rate=funding_rate,
            note="Live USDT-M Futures data.",
        )
    ]
    entries.extend(
        ExchangeBreakdown(
            exchange=name,
            status="NOT_YET_IMPLEMENTED",
            open_interest=None,
            funding_rate=None,
            note="No client integrated for this exchange yet.",
        )
        for name in _UNINTEGRATED_EXCHANGES
    )
    return entries


def _bucket_liquidations(events: list, cluster_count: int = LIQUIDATION_CLUSTER_COUNT) -> list[LiquidationCluster]:
    if not events:
        return []
    prices = [e.price for e in events]
    low, high = min(prices), max(prices)
    if low == high:
        total = sum(e.amount_usd for e in events)
        return [LiquidationCluster(price_low=low, price_high=high, total_usd=total, event_count=len(events))]

    width = (high - low) / cluster_count
    totals = [0.0] * cluster_count
    counts = [0] * cluster_count
    for event in events:
        idx = min(cluster_count - 1, int((event.price - low) / width))
        totals[idx] += event.amount_usd
        counts[idx] += 1

    return [
        LiquidationCluster(
            price_low=low + i * width, price_high=low + (i + 1) * width, total_usd=totals[i], event_count=counts[i]
        )
        for i in range(cluster_count)
        if counts[i] > 0
    ]


async def get_derivatives_snapshot(db: AsyncSession, base_asset: str) -> AssetDerivatives:
    symbol = to_trading_pair(base_asset)
    funding = await get_latest_funding(db, symbol)
    funding_history_rows = await _get_funding_history(db, symbol)
    open_interest = await get_latest_open_interest(db, symbol)
    oi_history = await get_recent_open_interest_history(db, symbol, limit=OI_HISTORY_LIMIT)
    liquidations = await get_recent_liquidations(db, limit=100, symbol=symbol)

    funding_trend = "NEUTRAL"
    if len(funding_history_rows) >= 2:
        first, last = funding_history_rows[0][1], funding_history_rows[-1][1]
        funding_trend = "UP" if last > first else "DOWN" if last < first else "NEUTRAL"

    oi_delta_percent = None
    if len(oi_history) >= 2 and oi_history[0].open_interest > 0:
        oi_delta_percent = (
            (oi_history[-1].open_interest - oi_history[0].open_interest) / oi_history[0].open_interest * 100.0
        )

    return AssetDerivatives(
        symbol=symbol,
        funding_rate=funding.funding_rate if funding else None,
        funding_history=funding_history_rows,
        funding_trend=funding_trend,
        open_interest=open_interest.open_interest if open_interest else None,
        open_interest_value=open_interest.open_interest_value if open_interest else None,
        oi_delta_percent=oi_delta_percent,
        liquidation_clusters=_bucket_liquidations(liquidations),
        exchange_breakdown=_exchange_breakdown(
            open_interest.open_interest if open_interest else None, funding.funding_rate if funding else None
        ),
    )


async def _get_funding_history(db: AsyncSession, symbol: str) -> list[tuple[int, float]]:
    rows = await get_recent_funding_history(db, symbol, limit=FUNDING_HISTORY_LIMIT)
    return [(row.funding_time, row.funding_rate) for row in rows]


# ---------------------------------------------------------------------------
# Whales tab
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssetWhales:
    symbol: str
    asset: str | None  # the on-chain asset this maps to (ETH/LINK), None if uncovered
    whale_score: float
    events: list[WhaleEvent]
    to_exchange_usd_24h: float
    from_exchange_usd_24h: float


async def get_whales_snapshot(db: AsyncSession, base_asset: str, limit: int = 30) -> AssetWhales:
    symbol = to_trading_pair(base_asset)
    snapshot = await get_whale_snapshot_for_symbol(db, symbol)
    events = await get_recent_whale_events(db, limit=limit, asset=base_asset.upper())
    factor = score_whales(snapshot)

    return AssetWhales(
        symbol=symbol,
        asset=base_asset.upper() if snapshot is not None else None,
        whale_score=factor.score,
        events=events,
        to_exchange_usd_24h=snapshot.to_exchange_usd if snapshot else 0.0,
        from_exchange_usd_24h=snapshot.from_exchange_usd if snapshot else 0.0,
    )


# ---------------------------------------------------------------------------
# News tab
# ---------------------------------------------------------------------------


async def get_news_snapshot(db: AsyncSession, base_asset: str, limit: int = 30) -> list[NewsArticle]:
    return await get_latest_news(db, limit=limit, symbol=base_asset.upper())


# ---------------------------------------------------------------------------
# Macro tab
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MacroInfluenceReading:
    id: str
    label: str
    current: float | None
    change_percent: float | None
    trend: str
    influence: str  # HIGH | LOW (LOW = tracked/displayed but not used_in_scoring)


async def get_macro_snapshot(db: AsyncSession) -> list[MacroInfluenceReading]:
    """Market-wide, not symbol-specific — the Macro Engine has no
    per-asset breakdown (see `app/intelligence/macro/`'s docstring) — but
    every asset page shows the same real macro backdrop, same as the
    Dashboard's Intelligence Card does."""
    readings: list[MacroInfluenceReading] = []
    for indicator_def in MACRO_INDICATORS:
        points = await get_latest_points(db, indicator_def.id, limit=2)
        if not points:
            readings.append(
                MacroInfluenceReading(
                    id=indicator_def.id,
                    label=indicator_def.label,
                    current=None,
                    change_percent=None,
                    trend="NEUTRAL",
                    influence="HIGH" if indicator_def.used_in_scoring else "LOW",
                )
            )
            continue

        current = points[0].value
        change_percent = None
        trend = "NEUTRAL"
        if len(points) > 1 and points[1].value != 0:
            change_percent = (current - points[1].value) / points[1].value * 100.0
            trend = "UP" if change_percent > 0 else "DOWN" if change_percent < 0 else "NEUTRAL"

        readings.append(
            MacroInfluenceReading(
                id=indicator_def.id,
                label=indicator_def.label,
                current=current,
                change_percent=change_percent,
                trend=trend,
                influence="HIGH" if indicator_def.used_in_scoring else "LOW",
            )
        )
    return readings


# ---------------------------------------------------------------------------
# Sentiment tab (radar)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SentimentRadar:
    news: float
    social: float | None  # no Social Engine exists yet — always None, see README
    whale: float
    technical: float
    macro: float
    market_score: float


@dataclass(frozen=True)
class AssetSentiment:
    result: SentimentResult
    radar: SentimentRadar


async def get_sentiment_snapshot(db: AsyncSession, base_asset: str, interval: str = "1h") -> AssetSentiment | None:
    symbol = to_trading_pair(base_asset)
    result = await compute_sentiment(db, symbol, interval)
    if result is None:
        return None

    radar = SentimentRadar(
        news=result.breakdown["news"].score,
        social=None,
        whale=result.breakdown["whales"].score,
        technical=result.breakdown["technical"].score,
        macro=result.breakdown["macro"].score,
        market_score=result.overall_score,
    )
    return AssetSentiment(result=result, radar=radar)


# ---------------------------------------------------------------------------
# AI Analysis tab
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AssetAnalysis:
    symbol: str
    interval: str
    direction: str
    confidence: float
    market_score: float
    entry: float | None
    stop: float | None
    tp1: float | None
    tp2: float | None
    tp3: float | None
    risk_reward: float | None
    reasons: list[str]
    scenarios: list[Scenario]
    risk: RiskAnalysis


async def get_analysis_snapshot(db: AsyncSession, base_asset: str, interval: str = "1h") -> AssetAnalysis | None:
    symbol = to_trading_pair(base_asset)
    ctx = await build_market_context(db, symbol, interval)
    if ctx is None:
        return None

    decision = analyze_market(ctx)
    scenarios = analyze_scenarios(ctx, decision)
    risk = analyze_risk(ctx, decision)
    plan = decision.risk

    return AssetAnalysis(
        symbol=symbol,
        interval=interval,
        direction=decision.direction,
        confidence=decision.confidence,
        market_score=decision.market_score,
        entry=plan.entry if plan else None,
        stop=plan.stop if plan else None,
        tp1=plan.tp1 if plan else None,
        tp2=plan.tp2 if plan else None,
        tp3=plan.tp3 if plan else None,
        risk_reward=plan.risk_reward_tp2 if plan else None,
        reasons=decision.reasons,
        scenarios=scenarios,
        risk=risk,
    )


# ---------------------------------------------------------------------------
# History tab
# ---------------------------------------------------------------------------


async def get_history_snapshot(
    db: AsyncSession, base_asset: str, interval: str = "1h", limit: int = HISTORY_LIMIT
) -> HistorySummary:
    symbol = to_trading_pair(base_asset)
    return await get_history_summary(db, symbol, interval, limit=limit)


# ---------------------------------------------------------------------------
# Correlation tab
# ---------------------------------------------------------------------------


async def get_correlation_snapshot(db: AsyncSession, base_asset: str, interval: str = "1h") -> list[CorrelationReading]:
    symbol = to_trading_pair(base_asset)
    return await compute_correlations(db, symbol, interval)


# ---------------------------------------------------------------------------
# Confidence Timeline / Explain Decision
# ---------------------------------------------------------------------------


async def get_timeline_snapshot(
    db: AsyncSession, base_asset: str, interval: str = "1h", limit: int = TIMELINE_LIMIT
) -> TimelineSummary:
    symbol = to_trading_pair(base_asset)
    return await get_timeline(db, symbol, interval, limit=limit)
