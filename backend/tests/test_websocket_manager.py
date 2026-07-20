from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.websocket import router as websocket_router
from app.services.websocket.manager import ConnectionManager, connection_manager

# A minimal app with just the WS route — avoids pulling in app.main's full
# lifespan (DB init + Binance-touching background tasks) for what is a
# unit test of the connection manager's fan-out behavior.
ws_test_app = FastAPI()
ws_test_app.include_router(websocket_router)


def test_single_client_receives_broadcast():
    connection_manager._connections.clear()

    with TestClient(ws_test_app) as client, client.websocket_connect("/ws/market") as ws:
        # TestClient's websocket_connect runs the ASGI app on a background
        # thread with its own event loop; broadcasting from the test's main
        # thread needs its own loop to drive `await websocket.send_json(...)`.
        import asyncio

        asyncio.run(connection_manager.broadcast("ticker", {"symbol": "BTCUSDT", "price": 65000}))

        message = ws.receive_json()
        assert message == {"channel": "ticker", "data": {"symbol": "BTCUSDT", "price": 65000}}


def test_disconnected_client_is_dropped_from_manager():
    connection_manager._connections.clear()

    with TestClient(ws_test_app) as client:
        with client.websocket_connect("/ws/market"):
            assert len(connection_manager._connections) == 1
        # Give the server-side handler a moment to process the disconnect.
        import time

        time.sleep(0.1)

    assert len(connection_manager._connections) == 0


def test_broadcast_with_no_clients_is_a_noop():
    manager = ConnectionManager()
    import asyncio

    asyncio.run(manager.broadcast("ticker", {"symbol": "BTCUSDT"}))  # must not raise
