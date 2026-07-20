from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.engine_state import engine_state
from app.core.redis import ping as redis_ping
from app.database.session import get_db
from app.schemas.status import EngineStatus, SymbolFeedStatus

router = APIRouter(prefix="/api/status", tags=["status"])
settings = get_settings()


async def _check_database(db: AsyncSession) -> bool:
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — health check, never raises
        return False


@router.get("", response_model=EngineStatus)
async def get_status(db: AsyncSession = Depends(get_db)) -> EngineStatus:
    database_connected = await _check_database(db)
    redis_connected = await redis_ping()

    symbol_feeds = [
        SymbolFeedStatus(
            symbol=symbol,
            last_trade_at=feed.last_trade_at.isoformat() if feed.last_trade_at else None,
            last_kline_at=feed.last_kline_at.isoformat() if feed.last_kline_at else None,
            last_funding_at=feed.last_funding_at.isoformat() if feed.last_funding_at else None,
        )
        for symbol, feed in engine_state.symbol_feeds.items()
    ]

    return EngineStatus(
        environment=settings.environment,
        database_connected=database_connected,
        redis_connected=redis_connected,
        binance_ws_state=engine_state.overall_ws_state,
        tracked_symbols=settings.symbol_list,
        tracked_timeframes=settings.timeframe_list,
        symbol_feeds=symbol_feeds,
        connected_frontend_clients=engine_state.connected_frontend_clients,
        uptime_seconds=round(engine_state.uptime_seconds, 1),
    )
