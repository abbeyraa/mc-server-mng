from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import require_role
from app.models.user import User
from app.services.server_controller import server_controller

router = APIRouter(prefix="/console", tags=["console"])


class CommandRequest(BaseModel):
    command: str


@router.post("/command")
async def send_command(
    body: CommandRequest,
    _: User = Depends(require_role("manager")),
):
    try:
        await server_controller.send_command(body.command)
        return {"ok": True}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
