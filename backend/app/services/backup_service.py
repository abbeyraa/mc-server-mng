import logging
import shutil
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.backup import BackupRecord

logger = logging.getLogger(__name__)


async def create_backup(
    db: AsyncSession,
    world_name: str,
    profile_id: int | None = None,
    trigger: str = "manual",
) -> BackupRecord:
    world_path = settings.worlds_dir / world_name
    if not world_path.exists():
        raise FileNotFoundError(f"World '{world_name}' not found")

    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    archive_name = f"{world_name}_{trigger}_{timestamp}"
    archive_path = settings.backups_dir / archive_name

    await _zip_directory(world_path, archive_path)

    zip_path = Path(str(archive_path) + ".zip")
    size = zip_path.stat().st_size

    record = BackupRecord(
        filename=zip_path.name,
        profile_id=profile_id,
        world_name=world_name,
        trigger=trigger,
        size_bytes=size,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    logger.info(f"Backup created: {zip_path.name} ({size} bytes)")
    return record


async def restore_backup(db: AsyncSession, backup_id: int) -> None:
    result = await db.execute(select(BackupRecord).where(BackupRecord.id == backup_id))
    record = result.scalar_one_or_none()
    if not record:
        raise FileNotFoundError(f"Backup {backup_id} not found")

    zip_path = settings.backups_dir / record.filename
    if not zip_path.exists():
        raise FileNotFoundError(f"Backup file missing: {record.filename}")

    world_path = settings.worlds_dir / record.world_name
    if world_path.exists():
        shutil.rmtree(world_path)

    shutil.unpack_archive(str(zip_path), str(settings.worlds_dir))
    logger.info(f"Restored world '{record.world_name}' from {record.filename}")


async def list_backups(db: AsyncSession) -> list[BackupRecord]:
    result = await db.execute(select(BackupRecord).order_by(BackupRecord.created_at.desc()))
    return list(result.scalars().all())


def get_backup_path(filename: str) -> Path:
    path = settings.backups_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Backup file not found: {filename}")
    return path


async def _zip_directory(source: Path, dest: Path) -> None:
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, shutil.make_archive, str(dest), "zip", str(source.parent), source.name)
