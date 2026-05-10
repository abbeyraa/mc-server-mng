import asyncio
import logging
import shutil
from pathlib import Path

import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)


def list_worlds(active_world: str | None = None) -> list[dict]:
    worlds_dir = settings.worlds_dir
    worlds_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for entry in worlds_dir.iterdir():
        if entry.is_dir():
            size = _dir_size(entry)
            result.append({
                "name": entry.name,
                "size_bytes": size,
                "is_active": entry.name == active_world,
            })
    return result


async def save_world_upload(filename: str, data: bytes) -> None:
    dest = settings.worlds_dir / filename
    dest.mkdir(parents=True, exist_ok=True)
    # Assume uploaded as .zip — extract
    zip_path = settings.worlds_dir / f"{filename}.zip"
    async with aiofiles.open(zip_path, "wb") as f:
        await f.write(data)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, shutil.unpack_archive, str(zip_path), str(settings.worlds_dir))
    zip_path.unlink(missing_ok=True)
    logger.info(f"World uploaded: {filename}")


async def delete_world(world_name: str) -> None:
    world_path = settings.worlds_dir / world_name
    if not world_path.exists():
        raise FileNotFoundError(f"World '{world_name}' not found")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, shutil.rmtree, str(world_path))
    logger.info(f"World deleted: {world_name}")


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
