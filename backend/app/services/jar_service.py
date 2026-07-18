import json
import logging
import re
import zipfile
from pathlib import Path

import aiofiles

from app.core.config import settings

logger = logging.getLogger(__name__)
VERSION_RE = re.compile(r"(?<!\d)(1\.\d+(?:\.\d+)?)(?!\d)")
SERVER_TYPES = ("paper", "purpur", "fabric", "forge", "spigot", "bukkit", "vanilla")


def _safe_jar_name(filename: str) -> str:
    safe_name = Path(filename).name
    if not safe_name.endswith(".jar"):
        raise ValueError("Only .jar files are allowed")
    return safe_name


def _jar_metadata(path: Path) -> dict[str, str | None]:
    metadata: dict[str, str | None] = {
        "minecraft_version": None,
        "server_type": _server_type_from_filename(path.name),
    }

    try:
        with zipfile.ZipFile(path) as jar:
            metadata.update(_metadata_from_version_json(jar))
    except (OSError, zipfile.BadZipFile):
        logger.warning("Unable to read jar metadata: %s", path)

    if not metadata["minecraft_version"]:
        metadata["minecraft_version"] = _minecraft_version_from_filename(path.name)
    return metadata


def _metadata_from_version_json(jar: zipfile.ZipFile) -> dict[str, str | None]:
    try:
        with jar.open("version.json") as version_file:
            version_data = json.load(version_file)
    except (KeyError, json.JSONDecodeError, OSError):
        return {}

    version = version_data.get("id") or version_data.get("name")
    return {
        "minecraft_version": str(version) if version else None,
        "server_type": "vanilla",
    }


def _minecraft_version_from_filename(filename: str) -> str | None:
    match = VERSION_RE.search(filename)
    return match.group(1) if match else None


def _server_type_from_filename(filename: str) -> str | None:
    lower_name = filename.lower()
    for server_type in SERVER_TYPES:
        if server_type in lower_name:
            return server_type
    return None


def _jar_info(path: Path) -> dict:
    return {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "path": str(path),
        **_jar_metadata(path),
    }


def list_jars() -> list[dict]:
    jars_dir = settings.server_jars_dir
    jars_dir.mkdir(parents=True, exist_ok=True)
    return [
        _jar_info(entry)
        for entry in sorted(jars_dir.iterdir())
        if entry.is_file() and entry.name.endswith(".jar")
    ]


async def save_jar(filename: str, data: bytes) -> dict:
    safe_name = _safe_jar_name(filename)
    jars_dir = settings.server_jars_dir
    jars_dir.mkdir(parents=True, exist_ok=True)
    dest = jars_dir / safe_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)
    logger.info("Server jar uploaded: %s", safe_name)
    return _jar_info(dest)


def delete_jar(filename: str) -> None:
    safe_name = _safe_jar_name(filename)
    jar_path = settings.server_jars_dir / safe_name
    if not jar_path.exists():
        raise FileNotFoundError(f"Jar '{safe_name}' not found")
    jar_path.unlink()
    logger.info("Server jar deleted: %s", safe_name)
