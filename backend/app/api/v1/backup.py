from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role, get_current_user
from app.models.user import User
from app.schemas.backup import BackupCreate, BackupRead, RestoreRequest
from app.services import backup_service, profile_service
from app.services.server_controller import server_controller

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("", response_model=list[BackupRead])
async def list_backups(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await backup_service.list_backups(db)


@router.post("", response_model=BackupRead)
async def create_backup(
    body: BackupCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    profile = None
    if body.profile_id:
        profile = await profile_service.get_profile(db, body.profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

    world_name = profile.world_name if profile else None
    if not world_name:
        raise HTTPException(status_code=400, detail="No world_name specified and no active profile")

    try:
        record = await backup_service.create_backup(db, world_name, body.profile_id, "manual")
        return record
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/restore")
async def restore_backup(
    body: RestoreRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    status = server_controller.get_status()
    if status["status"] in ("running", "starting"):
        raise HTTPException(status_code=409, detail="Stop the server before restoring a backup")
    try:
        await backup_service.restore_backup(db, body.backup_id)
        return {"ok": True}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    records = await backup_service.list_backups(db)
    record = next((r for r in records if r.id == backup_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Backup not found")
    try:
        path = backup_service.get_backup_path(record.filename)
        return FileResponse(path=str(path), filename=record.filename, media_type="application/zip")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
