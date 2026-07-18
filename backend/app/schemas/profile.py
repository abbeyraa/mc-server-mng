from datetime import datetime
import re

from pydantic import BaseModel, field_validator


RAM_RE = re.compile(r"^(\d+)\s*([KMGT]?B?)$", re.IGNORECASE)


def normalize_ram(value: str) -> str:
    match = RAM_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("RAM must use Java units, e.g. 1024M, 4G, 10GB")

    amount, unit = match.groups()
    unit = unit.upper()
    if unit.endswith("B"):
        unit = unit[:-1]
    if not unit:
        unit = "M"
    return f"{amount}{unit}"


class ProfileBase(BaseModel):
    name: str
    minecraft_version: str
    server_type: str = "vanilla"
    jar_path: str
    world_name: str
    ram_min: str = "1G"
    ram_max: str = "4G"
    java_args: list[str] = []
    mods_path: str | None = None

    @field_validator("ram_min", "ram_max")
    @classmethod
    def validate_ram(cls, value: str) -> str:
        return normalize_ram(value)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileRead(ProfileBase):
    id: int
    is_active: bool
    jar_exists: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
