from pydantic import BaseModel


class WorldInfo(BaseModel):
    name: str
    size_bytes: int
    is_active: bool


class WorldSelectRequest(BaseModel):
    world_name: str
    profile_id: int
