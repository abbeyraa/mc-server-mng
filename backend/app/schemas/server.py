from typing import Literal
from pydantic import BaseModel


class ServerStatus(BaseModel):
    status: Literal["running", "stopped", "crashed", "starting", "stopping"]
    pid: int | None
    uptime_seconds: float | None
    active_profile: str | None


class ActionResponse(BaseModel):
    ok: bool
    message: str
