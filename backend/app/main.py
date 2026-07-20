import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ai,
    backtesting,
    candles,
    chat,
    funding,
    indicators,
    liquidations,
    macro,
    market,
    news,
    open_interest,
    portfolio,
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
from app.services.binance.ws_client import ConnectionState
from app.services.websocket.manager import connection_manager
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
    description="Backend for the AIMAG AI trading terminal. Sprint 2 adds a real-time "
    "Binance-backed Data Engine (REST + WebSocket ingestion, indicators, Postgres/Redis "
    "storage). AI signal generation and trade decisions are explicitly out of scope here — "
    "see app/api/signals.py, which still serves mock data pending Sprint 3.",
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

# Still mock this sprint (portfolio, news, whales, liquidations, macro, backtesting, chat).
# signals.router is superseded by ai.router for AI analysis but stays mounted for now
# since the frontend's other mock-data consumers haven't been migrated yet.
app.include_router(signals.router)
app.include_router(portfolio.router)
app.include_router(news.router)
app.include_router(whales.router)
app.include_router(liquidations.router)
app.include_router(macro.router)
app.include_router(backtesting.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
