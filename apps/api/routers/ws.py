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

def handle_bybit_message(message):
    """Callback for messages coming from Bybit"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(json.dumps(message)))
    except RuntimeError:
        # If no running loop, we can't broadcast easily without setting up a background task.
        # This handles the case where Bybit's sync callback fires in a different thread.
        # A more robust solution uses asyncio.run_coroutine_threadsafe with a reference to the main loop.
        pass

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
