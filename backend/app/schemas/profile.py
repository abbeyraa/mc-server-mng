from datetime import datetime
from pydantic import BaseModel


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


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class ProfileRead(ProfileBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
