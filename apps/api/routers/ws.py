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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

import threading

# Global reference to the main event loop
main_loop = None

def handle_bybit_message(message):
    """Callback for messages coming from Bybit (runs in a background thread)"""
    global main_loop
    if main_loop and main_loop.is_running():
        # Safely schedule the broadcast on the main async event loop
        asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(message)), main_loop)

# Initialize Bybit WebSocket globally so it runs once
bybit_ws = None

def start_bybit_stream():
    global bybit_ws
    if bybit_ws is None:
        try:
            bybit_ws = BybitWebSocket(testnet=settings.BYBIT_TESTNET, channel_type="linear")
            # Subscribe to public trades for BTCUSDT
            bybit_ws.trade_stream(symbol="BTCUSDT", callback=handle_bybit_message)
            # Subscribe to orderbook (depth 50)
            bybit_ws.orderbook_stream(depth=50, symbol="BTCUSDT", callback=handle_bybit_message)
        except Exception as e:
            print(f"Failed to start Bybit WS: {e}")

@router.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    # Start the Bybit connection in a separate thread so it doesn't block FastAPI startup
    threading.Thread(target=start_bybit_stream, daemon=True).start()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect client messages in this uni-directional data stream MVP
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
