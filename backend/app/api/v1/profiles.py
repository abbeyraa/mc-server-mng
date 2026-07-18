import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role, get_current_user
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileRead
from app.services import backup_service, profile_service
from app.services.server_controller import server_controller

router = APIRouter(prefix="/profiles", tags=["profiles"])
logger = logging.getLogger(__name__)


def _serialize(profile) -> ProfileRead:
    data = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    if isinstance(data.get("java_args"), str):
        data["java_args"] = json.loads(data["java_args"])
    data["jar_exists"] = Path(profile.jar_path).exists()
    return ProfileRead(**data)


@router.get("", response_model=list[ProfileRead])
async def list_profiles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    profiles = await profile_service.list_profiles(db)
    return [_serialize(p) for p in profiles]


@router.post("", response_model=ProfileRead)
async def create_profile(
    body: ProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    profile = await profile_service.create_profile(db, body)
    return _serialize(profile)


@router.put("/{profile_id}", response_model=ProfileRead)
async def update_profile(
    profile_id: int,
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    try:
        profile = await profile_service.update_profile(db, profile_id, body)
        return _serialize(profile)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    try:
        await profile_service.delete_profile(db, profile_id)
        return {"ok": True}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{profile_id}/activate")
async def activate_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    profile = await profile_service.get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        status = server_controller.get_status()
        if status["status"] in ("running", "starting"):
            logger.info("Stopping server before profile switch")
            await server_controller.stop()

        active_profiles = [p for p in await profile_service.list_profiles(db) if p.is_active]
        for active_profile in active_profiles:
            if active_profile.world_name:
                try:
                    await backup_service.create_backup(
                        db,
                        active_profile.world_name,
                        active_profile.id,
                        trigger="pre-switch",
                    )
                except Exception as e:
                    logger.warning(f"Pre-switch backup failed: {e}")

        target = await profile_service.set_active_profile(db, profile_id)
        await server_controller.start(target)
        logger.info(f"Profile {target.name} activated and server started")
        return {"ok": True, "message": "Profile activated and server restarted"}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
