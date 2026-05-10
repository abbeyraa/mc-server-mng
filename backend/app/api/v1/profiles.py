import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_role, get_current_user
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileRead
from app.services import profile_service
from app.workers.tasks import activate_profile_task

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _serialize(profile) -> ProfileRead:
    data = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    if isinstance(data.get("java_args"), str):
        data["java_args"] = json.loads(data["java_args"])
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
    task = activate_profile_task.delay(profile_id)
    return {"ok": True, "task_id": task.id, "message": "Profile activation queued"}
