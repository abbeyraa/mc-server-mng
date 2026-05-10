import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="activate_profile")
def activate_profile_task(self, profile_id: int):
    """Stop server, backup world, activate profile, start server."""
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.services.profile_service import get_profile, set_active_profile
        from app.services.backup_service import create_backup
        from app.services.server_controller import server_controller

        async with AsyncSessionLocal() as db:
            profile = await get_profile(db, profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")

            # Stop if running
            status = server_controller.get_status()
            if status["status"] in ("running", "starting"):
                logger.info("Stopping server before profile switch")
                await server_controller.stop()

            # Backup current world if active profile exists
            active_profiles = [p for p in await _get_all_active(db)]
            for ap in active_profiles:
                if ap.world_name:
                    try:
                        await create_backup(db, ap.world_name, ap.id, trigger="pre-switch")
                    except Exception as e:
                        logger.warning(f"Pre-switch backup failed: {e}")

            # Activate new profile
            await set_active_profile(db, profile_id)

            # Start server
            await server_controller.start(profile)
            logger.info(f"Profile {profile.name} activated and server started")

    _run_async(_run())


async def _get_all_active(db):
    from sqlalchemy import select
    from app.models.profile import ServerProfile
    result = await db.execute(select(ServerProfile).where(ServerProfile.is_active == True))
    return result.scalars().all()


@celery_app.task(bind=True, name="create_backup")
def create_backup_task(self, world_name: str, profile_id: int | None, trigger: str = "manual"):
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.services.backup_service import create_backup
        async with AsyncSessionLocal() as db:
            record = await create_backup(db, world_name, profile_id, trigger)
            return record.id

    return _run_async(_run())
