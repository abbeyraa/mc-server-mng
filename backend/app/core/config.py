from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-to-a-random-secret-key-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/mc_manager.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    DATA_DIR: Path = Path("./data")
    LOGS_DIR: Path = Path("./logs")

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"

    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def worlds_dir(self) -> Path:
        return self.DATA_DIR / "worlds"

    @property
    def mods_dir(self) -> Path:
        return self.DATA_DIR / "mods"

    @property
    def backups_dir(self) -> Path:
        return self.DATA_DIR / "backups"

    @property
    def server_jars_dir(self) -> Path:
        return self.DATA_DIR / "server_jars"

    @property
    def server_log_path(self) -> Path:
        return self.LOGS_DIR / "server.log"

    class Config:
        env_file = ".env"


settings = Settings()
