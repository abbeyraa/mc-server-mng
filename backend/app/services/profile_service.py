import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import ServerProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate

logger = logging.getLogger(__name__)


async def list_profiles(db: AsyncSession) -> list[ServerProfile]:
    result = await db.execute(select(ServerProfile).order_by(ServerProfile.created_at))
    return list(result.scalars().all())


async def get_profile(db: AsyncSession, profile_id: int) -> ServerProfile | None:
    result = await db.execute(select(ServerProfile).where(ServerProfile.id == profile_id))
    return result.scalar_one_or_none()


async def create_profile(db: AsyncSession, data: ProfileCreate) -> ServerProfile:
    profile = ServerProfile(
        **data.model_dump(exclude={"java_args"}),
        java_args=json.dumps(data.java_args),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_profile(db: AsyncSession, profile_id: int, data: ProfileUpdate) -> ServerProfile:
    profile = await get_profile(db, profile_id)
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")
    for field, value in data.model_dump(exclude={"java_args"}).items():
        setattr(profile, field, value)
    profile.java_args = json.dumps(data.java_args)
    await db.commit()
    await db.refresh(profile)
    return profile


async def delete_profile(db: AsyncSession, profile_id: int) -> None:
    profile = await get_profile(db, profile_id)
    if not profile:
        raise ValueError(f"Profile {profile_id} not found")
    await db.delete(profile)
    await db.commit()


async def set_active_profile(db: AsyncSession, profile_id: int) -> ServerProfile:
    # Deactivate all
    all_profiles = await list_profiles(db)
    for p in all_profiles:
        p.is_active = False
    # Activate target
    target = await get_profile(db, profile_id)
    if not target:
        raise ValueError(f"Profile {profile_id} not found")
    target.is_active = True
    await db.commit()
    await db.refresh(target)
    return target
