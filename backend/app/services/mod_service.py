import logging
from pathlib import Path

import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)

DISABLED_SUFFIX = ".disabled"


def list_mods(mods_path: str | None = None) -> list[dict]:
    mods_dir = Path(mods_path) if mods_path else settings.mods_dir
    mods_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for entry in mods_dir.iterdir():
        if entry.is_file():
            enabled = not entry.name.endswith(DISABLED_SUFFIX)
            display_name = entry.name.removesuffix(DISABLED_SUFFIX)
            result.append({
                "filename": display_name,
                "size_bytes": entry.stat().st_size,
                "enabled": enabled,
            })
    return result


async def save_mod(filename: str, data: bytes, mods_path: str | None = None) -> None:
    mods_dir = Path(mods_path) if mods_path else settings.mods_dir
    mods_dir.mkdir(parents=True, exist_ok=True)
    dest = mods_dir / filename
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)
    logger.info(f"Mod uploaded: {filename}")


def toggle_mod(filename: str, enabled: bool, mods_path: str | None = None) -> None:
    mods_dir = Path(mods_path) if mods_path else settings.mods_dir
    enabled_path = mods_dir / filename
    disabled_path = mods_dir / f"{filename}{DISABLED_SUFFIX}"

    if enabled:
        if disabled_path.exists():
            disabled_path.rename(enabled_path)
        elif not enabled_path.exists():
            raise FileNotFoundError(f"Mod '{filename}' not found")
    else:
        if enabled_path.exists():
            enabled_path.rename(disabled_path)
        elif not disabled_path.exists():
            raise FileNotFoundError(f"Mod '{filename}' not found")


def delete_mod(filename: str, mods_path: str | None = None) -> None:
    mods_dir = Path(mods_path) if mods_path else settings.mods_dir
    for name in [filename, f"{filename}{DISABLED_SUFFIX}"]:
        p = mods_dir / name
        if p.exists():
            p.unlink()
            logger.info(f"Mod deleted: {name}")
            return
    raise FileNotFoundError(f"Mod '{filename}' not found")
