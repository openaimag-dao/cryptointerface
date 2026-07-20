"""Resilient WebSocket client for Binance USDT-M Futures combined streams.

Splits the configured symbols/timeframes across one or more connections
(see `streams.chunk_streams`), and keeps each connection alive
independently with exponential-backoff reconnect and an application-level
heartbeat watchdog (in addition to the WS protocol ping/pong that the
`websockets` library handles automatically).
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Literal

import websockets

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.binance.parsers import StreamEvent, parse_stream_message
from app.services.binance.streams import build_combined_stream_url, build_streams, chunk_streams
from app.utils.retry import compute_backoff_delay

logger = get_logger(__name__)
settings = get_settings()

ConnectionState = Literal["connecting", "connected", "disconnected"]
OnEventCallback = Callable[[StreamEvent], Awaitable[None]]
OnStateChangeCallback = Callable[[int, ConnectionState], Awaitable[None]]


class HeartbeatTimeout(Exception):
    """Raised when no message has arrived within the heartbeat window."""


class BinanceWebSocketClient:
    def __init__(
        self,
        symbols: list[str],
        timeframes: list[str],
        on_event: OnEventCallback,
        on_state_change: OnStateChangeCallback | None = None,
        base_url: str | None = None,
    ) -> None:
        self._symbols = symbols
        self._timeframes = timeframes
        self._on_event = on_event
        self._on_state_change = on_state_change
        self._base_url = base_url or settings.binance_ws_base_url
        self._stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        streams = build_streams(self._symbols, self._timeframes)
        chunks = chunk_streams(streams)
        logger.info("ws_client_starting", extra={"num_connections": len(chunks), "num_streams": len(streams)})
        self._tasks = [asyncio.create_task(self._run_connection(chunk, idx)) for idx, chunk in enumerate(chunks)]
        await asyncio.gather(*self._tasks)

    async def stop(self) -> None:
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _set_state(self, connection_index: int, state: ConnectionState) -> None:
        if self._on_state_change:
            await self._on_state_change(connection_index, state)

    async def _run_connection(self, streams: list[str], connection_index: int) -> None:
        url = build_combined_stream_url(streams, self._base_url)
        attempt = 0

        while not self._stop_event.is_set():
            attempt += 1
            await self._set_state(connection_index, "connecting")
            try:
                async with websockets.connect(
                    url,
                    ping_interval=settings.ws_heartbeat_interval_seconds,
                    ping_timeout=settings.ws_heartbeat_interval_seconds * 2,
                    close_timeout=5,
                ) as ws:
                    logger.info(
                        "ws_connected",
                        extra={"connection_index": connection_index, "num_streams": len(streams)},
                    )
                    attempt = 0
                    await self._set_state(connection_index, "connected")
                    await self._consume(ws, connection_index)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — any failure should trigger reconnect, not crash the task
                logger.warning(
                    "ws_connection_error",
                    extra={"connection_index": connection_index, "attempt": attempt, "error": str(exc)},
                )
                await self._set_state(connection_index, "disconnected")

            if self._stop_event.is_set():
                break

            delay = compute_backoff_delay(
                attempt, settings.ws_reconnect_min_delay_seconds, settings.ws_reconnect_max_delay_seconds
            )
            logger.info(
                "ws_reconnecting",
                extra={"connection_index": connection_index, "delay_seconds": round(delay, 2)},
            )
            await asyncio.sleep(delay)

    async def _consume(self, ws: websockets.WebSocketClientProtocol, connection_index: int) -> None:
        heartbeat_timeout = settings.ws_heartbeat_interval_seconds * 3

        while not self._stop_event.is_set():
            try:
                raw_message = await asyncio.wait_for(ws.recv(), timeout=heartbeat_timeout)
            except TimeoutError as exc:
                logger.warning("ws_heartbeat_timeout", extra={"connection_index": connection_index})
                raise HeartbeatTimeout("No message received within heartbeat window") from exc

            try:
                payload = json.loads(raw_message)
            except (json.JSONDecodeError, TypeError):
                logger.warning("ws_invalid_message", extra={"connection_index": connection_index})
                continue

            event = parse_stream_message(payload)
            if event is not None:
                await self._on_event(event)
