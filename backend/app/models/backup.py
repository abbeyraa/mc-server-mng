from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BackupRecord(Base):
    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("server_profiles.id"), nullable=True)
    world_name: Mapped[str] = mapped_column(String(128), nullable=False)
    trigger: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
