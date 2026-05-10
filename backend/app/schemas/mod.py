from pydantic import BaseModel


class ModInfo(BaseModel):
    filename: str
    size_bytes: int
    enabled: bool


class ModToggleRequest(BaseModel):
    filename: str
    enabled: bool
