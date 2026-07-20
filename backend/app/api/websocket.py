from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket.manager import connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket) -> None:
    """Live market feed for the frontend: ticker/candle/indicator/funding/trade
    updates, fanned out from the Binance-backed Data Engine. No client->server
    protocol beyond the connection itself — this is receive-only from the
    browser's perspective.
    """
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
