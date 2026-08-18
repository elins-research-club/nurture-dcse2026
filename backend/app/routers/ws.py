from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import manager
from typing import Dict

router = APIRouter()

@router.websocket("/ws/{node_id}")
async def websocket_endpoint(websocket: WebSocket, node_id: str):
    await manager.connect(node_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(node_id, websocket)

@router.get("/ws/status")
async def get_ws_status() -> Dict[str, Dict[str, int]]:
    counts = {node_id: len(websockets) for node_id, websockets in manager.active.items()}
    return {"connected_clients": counts}
