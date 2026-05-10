from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ServerProfile(Base):
    __tablename__ = "server_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    minecraft_version: Mapped[str] = mapped_column(String(32), nullable=False)
    server_type: Mapped[str] = mapped_column(String(32), nullable=False, default="vanilla")
    jar_path: Mapped[str] = mapped_column(String(512), nullable=False)
    world_name: Mapped[str] = mapped_column(String(128), nullable=False)
    ram_min: Mapped[str] = mapped_column(String(16), nullable=False, default="1G")
    ram_max: Mapped[str] = mapped_column(String(16), nullable=False, default="4G")
    java_args: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    mods_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
