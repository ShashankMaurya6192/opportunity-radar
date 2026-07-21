from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Opportunity Radar"
    app_version: str = "0.8.0"
    environment: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./opportunity_radar_v3.db"

    discovery_concurrency: int = 4
    discovery_schedule_hours: int = 24

    request_timeout_seconds: float = 20.0
    crawler_max_pages: int = 12
    crawler_concurrency: int = 4

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
