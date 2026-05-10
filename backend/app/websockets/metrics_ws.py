import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.services.monitoring_service import get_metrics
from app.services.server_controller import server_controller

logger = logging.getLogger(__name__)


async def metrics_endpoint(websocket: WebSocket, token: str):
    try:
        decode_token(token)
    except ValueError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    try:
        while True:
            metrics = get_metrics()
            status_info = server_controller.get_status()
            payload = {**metrics, **status_info}
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except (WebSocketDisconnect, Exception):
        pass
