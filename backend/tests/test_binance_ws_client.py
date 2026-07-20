import asyncio
import json

import pytest
import websockets

from app.services.binance.parsers import KlineEvent
from app.services.binance.ws_client import BinanceWebSocketClient

KLINE_MESSAGE = {
    "stream": "btcusdt@kline_1m",
    "data": {
        "e": "kline",
        "E": 1,
        "s": "BTCUSDT",
        "k": {
            "t": 1_700_000_000_000,
            "T": 1_700_000_059_999,
            "s": "BTCUSDT",
            "i": "1m",
            "f": 1,
            "L": 2,
            "o": "100",
            "c": "101",
            "h": "102",
            "l": "99",
            "v": "10",
            "n": 5,
            "x": True,
            "q": "1000",
            "V": "5",
            "Q": "500",
            "B": "0",
        },
    },
}


@pytest.mark.asyncio
async def test_ws_client_receives_and_reconnects(monkeypatch):
    received: list[KlineEvent] = []
    states: list[tuple[int, str]] = []

    async def on_event(event):
        received.append(event)

    async def on_state(idx, state):
        states.append((idx, state))

    async def fake_server(ws):
        await ws.send(json.dumps(KLINE_MESSAGE))
        await asyncio.sleep(0.2)
        await ws.close()  # forces the client to detect a drop and reconnect

    server = await websockets.serve(fake_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]

    monkeypatch.setattr(
        "app.services.binance.ws_client.build_combined_stream_url",
        lambda streams, base_url=None: f"ws://localhost:{port}",
    )

    client = BinanceWebSocketClient(
        symbols=["BTCUSDT"],
        timeframes=["1m"],
        on_event=on_event,
        on_state_change=on_state,
    )

    task = asyncio.create_task(client.start())
    try:
        # Poll instead of a fixed sleep: under a loaded test suite, backoff
        # + reconnect can occasionally take longer than a tight fixed delay.
        for _ in range(100):  # up to ~10s
            if len(received) >= 2:
                break
            await asyncio.sleep(0.1)
        await client.stop()
    finally:
        server.close()
        await server.wait_closed()
        task.cancel()

    assert len(received) >= 2  # received the same message before AND after the forced reconnect
    assert all(isinstance(event, KlineEvent) and event.symbol == "BTCUSDT" for event in received)

    seen_states = [state for _, state in states]
    assert seen_states.count("connected") >= 2  # proves it actually reconnected
    assert "disconnected" in seen_states
