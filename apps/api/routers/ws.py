from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from pybit.unified_trading import WebSocket as BybitWebSocket
from apps.api.core.config import settings

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.bybit_ws = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass # Handle dead connections if needed

manager = ConnectionManager()

def handle_bybit_message(message):
    """Callback for messages coming from Bybit"""
    # Use asyncio.run_coroutine_threadsafe to send to our FastApi WebSocket manager
    # if we are doing this from a separate thread, but pybit callbacks are synchronous
    # so we create a new event loop or use an existing one to broadcast.
    # A robust implementation would use a background task with queues.
    # For now, we simulate broadcasting.
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(json.dumps(message)))
    except Exception:
        # If no running loop, we can just print or ignore for now
        print(f"Bybit Message: {message}")

# We would initialize Bybit WebSocket here in a real scenario
# and subscribe to the channels (e.g., 'publicTrade.BTCUSDT')
# ws = BybitWebSocket(testnet=settings.BYBIT_TESTNET, channel_type="linear")
# ws.trade_stream(symbol="BTCUSDT", callback=handle_bybit_message)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any client messages if we want bidirectional
            data = await websocket.receive_text()
            # Echo back for test purposes
            await manager.broadcast(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
