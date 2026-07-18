import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.api.v1.playit import attach_manager
from app.services.server_controller import server_controller
from app.core.config import settings

logger = logging.getLogger(__name__)

LOG_HISTORY_LINES = 100


async def console_endpoint(websocket: WebSocket, token: str):
    # Authenticate via query param token
    try:
        decode_token(token)
    except ValueError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    queue = server_controller.subscribe_console()

    # Send recent log history
    try:
        with open(settings.server_log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        history = lines[-LOG_HISTORY_LINES:]
        for line in history:
            await websocket.send_text(line)
    except FileNotFoundError:
        pass

    recv_task = asyncio.create_task(_receive_commands(websocket))
    try:
        while True:
            try:
                line = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_text(line)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text("")
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        recv_task.cancel()
        server_controller.unsubscribe_console(queue)


async def playit_console_endpoint(websocket: WebSocket, token: str):
    try:
        decode_token(token)
    except ValueError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    queue, history = attach_manager.subscribe_console()

    try:
        for line in history:
            await websocket.send_text(f"{line}\n")

        while True:
            try:
                line = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_text(f"{line}\n")
            except asyncio.TimeoutError:
                await websocket.send_text("")
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        attach_manager.unsubscribe_console(queue)


async def _receive_commands(websocket: WebSocket):
    try:
        while True:
            cmd = await websocket.receive_text()
            if cmd.strip():
                try:
                    await server_controller.send_command(cmd.strip())
                except RuntimeError as e:
                    await websocket.send_text(f"[ERROR] {e}\n")
    except (WebSocketDisconnect, Exception):
        pass
