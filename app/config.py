from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Opportunity Radar"
    app_version: str = "0.5.0"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./opportunity_radar.db"
    log_level: str = "INFO"
    discovery_concurrency: int = 5
    discovery_max_results: int = 50
    discovery_schedule_hours: int = 24
    request_timeout_seconds: float = 15.0
    data_dir: Path = Path("data")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="OR_", extra="ignore")

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)
        Path("backups").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


settings = get_settings()
