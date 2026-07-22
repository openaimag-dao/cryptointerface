import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ai,
    assets,
    backtesting,
    candles,
    chat,
    dashboard_intelligence,
    funding,
    indicators,
    liquidations,
    llm,
    macro,
    market,
    news,
    open_interest,
    portfolio,
    sentiment,
    signals,
    status,
    websocket,
    whales,
)
from app.core.config import get_settings
from app.core.engine_state import engine_state
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis
from app.database.session import AsyncSessionLocal, dispose_engine, init_models
from app.intelligence.scheduler.tasks import (
    run_llm_explanation_refresh,
    run_macro_poller,
    run_news_poller,
    run_sentiment_recompute,
    run_whale_poller,
)
from app.services.binance.ws_client import ConnectionState
from app.services.websocket.manager import connection_manager
from app.tasks.coingecko_fallback import run_coingecko_fallback_poller
from app.tasks.historical_loader import run_historical_backfill
from app.tasks.live_feed import LiveFeedService
from app.tasks.open_interest_poller import run_open_interest_poller

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

_background_tasks: list[asyncio.Task] = []
_stop_event = asyncio.Event()


async def _on_ws_state_change(connection_index: int, state: ConnectionState) -> None:
    engine_state.set_ws_state(connection_index, state)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_starting", extra={"environment": settings.environment, "symbols": settings.symbol_list})
    await init_models()

    live_feed = LiveFeedService(broadcast=connection_manager.broadcast, on_state_change=_on_ws_state_change)

    # Historical backfill, the live WS feed, and OI polling all run in the
    # background so the app is immediately ready to serve requests (health
    # checks, static pages) while the Data Engine spins up behind it.
    _background_tasks.append(asyncio.create_task(run_historical_backfill(AsyncSessionLocal)))
    _background_tasks.append(asyncio.create_task(live_feed.start()))
    _background_tasks.append(asyncio.create_task(run_open_interest_poller(stop_event=_stop_event)))
    # CoinGecko ticker fallback — dormant while the Binance WS is connected,
    # only polls when it isn't (see app/tasks/coingecko_fallback.py).
    _background_tasks.append(
        asyncio.create_task(
            run_coingecko_fallback_poller(broadcast=connection_manager.broadcast, stop_event=_stop_event)
        )
    )
    # Sprint 4: Intelligence Layer schedulers (app/intelligence/scheduler/).
    _background_tasks.append(asyncio.create_task(run_macro_poller(stop_event=_stop_event)))
    _background_tasks.append(asyncio.create_task(run_news_poller(stop_event=_stop_event)))
    _background_tasks.append(asyncio.create_task(run_whale_poller(stop_event=_stop_event)))
    _background_tasks.append(asyncio.create_task(run_sentiment_recompute(stop_event=_stop_event)))
    _background_tasks.append(asyncio.create_task(run_llm_explanation_refresh(stop_event=_stop_event)))

    yield

    logger.info("app_stopping")
    _stop_event.set()
    await live_feed.stop()
    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    await dispose_engine()
    await close_redis()


app = FastAPI(
    title="AIMAG AI Terminal API",
    description="Backend for the AIMAG AI trading terminal: a real-time Binance-backed Data "
    "Engine (REST + WebSocket ingestion, indicators, Postgres/Redis storage) feeding a "
    "deterministic AI Decision Engine (no LLM, no trade execution — see AI_ENGINE.md), a Sprint 4 "
    "Intelligence Layer (macro/news/whales/sentiment/LLM-explanation, see app/intelligence/), a "
    "Claude-backed AI Chat assistant, and a Sprint 5 Backtesting Engine that replays the "
    "unmodified Decision Engine bar by bar with no look-ahead (see app/backtesting/). "
    "Portfolio still serves mock data pending a future sprint.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Real-time Data Engine endpoints
app.include_router(market.router)
app.include_router(candles.router)
app.include_router(indicators.router)
app.include_router(funding.router)
app.include_router(open_interest.router)
app.include_router(status.router)
app.include_router(websocket.router)

# Sprint 3: deterministic AI Decision Engine (analysis only, no trade execution)
app.include_router(ai.router)

# Real: signals.router batches the AI Decision Engine across the watchlist;
# liquidations.router is fed by Binance's forceOrder WS stream; chat.router
# answers with Anthropic Claude grounded in a live watchlist snapshot (the
# Decision Engine itself stays deterministic/no-LLM — see
# app/services/claude_chat.py).
app.include_router(signals.router)
app.include_router(liquidations.router)
app.include_router(chat.router)

# Sprint 4: Intelligence Layer (app/intelligence/) — macro.router's
# /indicators is real (/events is still a mock economic calendar);
# news.router is real (RSS + deterministic classifier, no LLM per
# article); whales.router is real (Etherscan-tracked transfers touching
# known exchange wallets, classified deterministically); sentiment/llm/
# dashboard_intelligence are entirely new and real.
app.include_router(macro.router)
app.include_router(news.router)
app.include_router(whales.router)
app.include_router(sentiment.router)
app.include_router(llm.router)
app.include_router(dashboard_intelligence.router)

# Sprint 5: Backtesting Engine (app/backtesting/) — replays the unmodified
# Sprint 3 Decision Engine bar by bar over historical candles, no
# look-ahead. See backend/README.md's Backtesting Engine section.
app.include_router(backtesting.router)

# Sprint 8: Asset Intelligence Dashboard (app/services/asset_service.py) —
# per-symbol research terminal, aggregates the existing engines above into
# `/api/assets/{symbol}/*`. No new computation, see backend/README.md.
app.include_router(assets.router)

# Still mock (portfolio) — out of scope until a future sprint.
app.include_router(portfolio.router)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
