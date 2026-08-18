import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, node_id: str, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            if node_id not in self.active:
                self.active[node_id] = set()
            self.active[node_id].add(ws)
            logger.info(f"WebSocket connected for node_id: {node_id}")

    async def disconnect(self, node_id: str, ws: WebSocket):
        async with self._lock:
            if node_id in self.active and ws in self.active[node_id]:
                self.active[node_id].remove(ws)
                if not self.active[node_id]:
                    del self.active[node_id]
                logger.info(f"WebSocket disconnected for node_id: {node_id}")

    async def broadcast(self, node_id: str, data: dict):
        async with self._lock:
            connections = self.active.get(node_id, set()).copy()

        if not connections:
            return

        async def send(ws: WebSocket):
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send WS message, removing stale connection: {e}")
                await self.disconnect(node_id, ws)

        await asyncio.gather(*(send(ws) for ws in connections), return_exceptions=True)

    async def broadcast_all(self, data: dict):
        async with self._lock:
            all_connections = [
                (node_id, ws) for node_id, websockets in self.active.items() for ws in websockets
            ]
            
        if not all_connections:
            return
            
        async def send(node_id: str, ws: WebSocket):
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send WS message to {node_id}, removing stale connection: {e}")
                await self.disconnect(node_id, ws)

        await asyncio.gather(*(send(node_id, ws) for node_id, ws in all_connections), return_exceptions=True)

manager = ConnectionManager()
