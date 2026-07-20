from typing import Literal

from app.schemas.base import CamelModel

ConnectionState = Literal["connected", "connecting", "disconnected"]


class SymbolFeedStatus(CamelModel):
    symbol: str
    last_trade_at: str | None = None
    last_kline_at: str | None = None
    last_funding_at: str | None = None


class EngineStatus(CamelModel):
    environment: str
    database_connected: bool
    redis_connected: bool
    binance_ws_state: ConnectionState
    tracked_symbols: list[str]
    tracked_timeframes: list[str]
    symbol_feeds: list[SymbolFeedStatus]
    connected_frontend_clients: int
    uptime_seconds: float
