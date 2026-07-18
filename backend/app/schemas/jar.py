from pydantic import BaseModel


class JarInfo(BaseModel):
    filename: str
    size_bytes: int
    path: str
    minecraft_version: str | None = None
    server_type: str | None = None
