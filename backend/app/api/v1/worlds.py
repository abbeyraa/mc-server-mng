from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role, get_current_user
from app.models.user import User
from app.schemas.world import WorldInfo, WorldSelectRequest
from app.services import world_service, profile_service

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("", response_model=list[WorldInfo])
async def list_worlds(_: User = Depends(get_current_user)):
    return world_service.list_worlds()


@router.post("/upload")
async def upload_world(
    file: UploadFile = File(...),
    _: User = Depends(require_role("admin")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    data = await file.read()
    name = file.filename.removesuffix(".zip")
    await world_service.save_world_upload(name, data)
    return {"ok": True, "world_name": name}


@router.post("/select")
async def select_world(
    body: WorldSelectRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    worlds = world_service.list_worlds()
    names = {w["name"] for w in worlds}
    if body.world_name not in names:
        raise HTTPException(status_code=404, detail=f"World '{body.world_name}' not found")
    try:
        profile = await profile_service.get_profile(db, body.profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile.world_name = body.world_name
        await db.commit()
        return {"ok": True, "world_name": body.world_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{world_name}")
async def delete_world(
    world_name: str,
    _: User = Depends(require_role("admin")),
):
    try:
        await world_service.delete_world(world_name)
        return {"ok": True}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
