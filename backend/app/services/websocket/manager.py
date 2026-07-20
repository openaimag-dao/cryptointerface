"""Fans out Data Engine updates to connected browser clients.

The live feed calls `broadcast(channel, payload)` on every tick; this
manager wraps that into `{"channel": ..., "data": ...}` envelopes and
pushes them to every currently-connected `/ws/market` client, dropping any
socket that fails to send (it'll reconnect from the browser side).
"""

from fastapi import WebSocket

from app.core.engine_state import engine_state
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        engine_state.connected_frontend_clients = len(self._connections)
        logger.info("frontend_ws_connected", extra={"total_clients": len(self._connections)})

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        engine_state.connected_frontend_clients = len(self._connections)
        logger.info("frontend_ws_disconnected", extra={"total_clients": len(self._connections)})

    async def broadcast(self, channel: str, payload: dict) -> None:
        if not self._connections:
            return

        envelope = {"channel": channel, "data": payload}
        dead: list[WebSocket] = []

        for connection in self._connections:
            try:
                await connection.send_json(envelope)
            except Exception:  # noqa: BLE001 — a broken client socket must not stop the broadcast
                dead.append(connection)

        for connection in dead:
            self.disconnect(connection)


connection_manager = ConnectionManager()
