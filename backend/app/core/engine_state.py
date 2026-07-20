"""In-memory runtime state for the Data Engine, read by `/api/status`.

Deliberately not persisted — this reflects "what is this process doing
right now" (WS connection state, last-seen timestamps, uptime), which is
meaningless across a restart.
"""

import time
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class SymbolFeedState:
    last_trade_at: datetime | None = None
    last_kline_at: datetime | None = None
    last_funding_at: datetime | None = None


class EngineState:
    def __init__(self) -> None:
        self._start_time = time.monotonic()
        self.ws_connection_states: dict[int, str] = {}
        self.symbol_feeds: dict[str, SymbolFeedState] = {}
        self.connected_frontend_clients: int = 0

    @property
    def uptime_seconds(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def overall_ws_state(self) -> str:
        states = self.ws_connection_states.values()
        if not states:
            return "disconnected"
        if all(state == "connected" for state in states):
            return "connected"
        if any(state == "connected" for state in states):
            return "connecting"  # partially up
        return "disconnected"

    def set_ws_state(self, connection_index: int, state: str) -> None:
        self.ws_connection_states[connection_index] = state

    def _feed(self, symbol: str) -> SymbolFeedState:
        return self.symbol_feeds.setdefault(symbol, SymbolFeedState())

    def mark_trade(self, symbol: str) -> None:
        self._feed(symbol).last_trade_at = datetime.now(UTC)

    def mark_kline(self, symbol: str) -> None:
        self._feed(symbol).last_kline_at = datetime.now(UTC)

    def mark_funding(self, symbol: str) -> None:
        self._feed(symbol).last_funding_at = datetime.now(UTC)


engine_state = EngineState()
