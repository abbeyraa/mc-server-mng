import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


class PlayitRead(BaseModel):
    domain: str
    join_address: str
    daemon_status: Literal["running", "unavailable"]
    attach_status: Literal["attached", "detached", "failed"]
    attach_message: str
    attach_started_at: datetime | None = None
    service_mode: Literal["native-systemd"]


class PlayitUpdate(BaseModel):
    domain: str = Field(min_length=1, max_length=253)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value: str) -> str:
        domain = value.strip().lower().rstrip(".")
        if not domain:
            raise ValueError("Domain is required")
        if "://" in domain or "/" in domain:
            raise ValueError("Use a hostname only, without protocol or path")
        if not HOSTNAME_RE.fullmatch(domain):
            raise ValueError("Enter a valid hostname")
        return domain
