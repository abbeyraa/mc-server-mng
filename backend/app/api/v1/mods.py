from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role, get_current_user
from app.models.user import User
from app.schemas.mod import ModInfo, ModToggleRequest
from app.services import mod_service, profile_service

router = APIRouter(prefix="/mods", tags=["mods"])


@router.get("", response_model=list[ModInfo])
async def list_mods(
    profile_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    mods_path = None
    if profile_id:
        profile = await profile_service.get_profile(db, profile_id)
        if profile:
            mods_path = profile.mods_path
    return mod_service.list_mods(mods_path)


@router.post("/upload")
async def upload_mod(
    file: UploadFile = File(...),
    profile_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    mods_path = None
    if profile_id:
        profile = await profile_service.get_profile(db, profile_id)
        if profile:
            mods_path = profile.mods_path
    data = await file.read()
    await mod_service.save_mod(file.filename, data, mods_path)
    return {"ok": True, "filename": file.filename}


@router.post("/toggle")
async def toggle_mod(
    body: ModToggleRequest,
    profile_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    mods_path = None
    if profile_id:
        profile = await profile_service.get_profile(db, profile_id)
        if profile:
            mods_path = profile.mods_path
    try:
        mod_service.toggle_mod(body.filename, body.enabled, mods_path)
        return {"ok": True}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{filename}")
async def delete_mod(
    filename: str,
    profile_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    mods_path = None
    if profile_id:
        profile = await profile_service.get_profile(db, profile_id)
        if profile:
            mods_path = profile.mods_path
    try:
        mod_service.delete_mod(filename, mods_path)
        return {"ok": True}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
