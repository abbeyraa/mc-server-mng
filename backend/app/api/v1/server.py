from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import require_role, get_current_user
from app.models.profile import ServerProfile
from app.models.user import User
from app.schemas.server import ServerStatus, ActionResponse
from app.services.server_controller import server_controller

router = APIRouter(prefix="/server", tags=["server"])


async def _get_active_profile(db: AsyncSession) -> ServerProfile | None:
    result = await db.execute(select(ServerProfile).where(ServerProfile.is_active == True))
    return result.scalar_one_or_none()


@router.get("/status", response_model=ServerStatus)
async def get_status(_: User = Depends(get_current_user)):
    return ServerStatus(**server_controller.get_status())


@router.post("/start", response_model=ActionResponse)
async def start_server(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    profile = await _get_active_profile(db)
    if not profile:
        raise HTTPException(status_code=400, detail="No active profile. Activate a profile first.")
    try:
        await server_controller.start(profile)
        return ActionResponse(ok=True, message="Server started")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/stop", response_model=ActionResponse)
async def stop_server(_: User = Depends(require_role("manager"))):
    try:
        await server_controller.stop()
        return ActionResponse(ok=True, message="Server stopped")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart", response_model=ActionResponse)
async def restart_server(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    profile = await _get_active_profile(db)
    if not profile:
        raise HTTPException(status_code=400, detail="No active profile")
    try:
        await server_controller.restart(profile)
        return ActionResponse(ok=True, message="Server restarted")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
