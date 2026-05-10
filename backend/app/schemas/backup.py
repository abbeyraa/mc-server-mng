from datetime import datetime
from pydantic import BaseModel


class BackupCreate(BaseModel):
    profile_id: int | None = None


class RestoreRequest(BaseModel):
    backup_id: int


class BackupRead(BaseModel):
    id: int
    filename: str
    profile_id: int | None
    world_name: str
    trigger: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True
