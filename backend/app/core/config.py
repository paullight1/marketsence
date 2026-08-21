from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketSense NG API"
    app_version: str = "0.5.0"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./marketsense.db"
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    sql_echo: bool = False

    auth_enabled: bool = False
    auth_secret: str = ""
    auth_username: str = ""
    auth_password_hash: str = ""
    auth_role: Literal["viewer", "analyst", "admin"] = "admin"
    auth_token_ttl_minutes: int = Field(default=30, ge=5, le=720)

    rate_limit_enabled: bool = False
    redis_url: str | None = None
    auth_login_limit_per_minute: int = Field(default=5, ge=1, le=120)
    read_limit_per_minute: int = Field(default=120, ge=1, le=10_000)
    write_limit_per_minute: int = Field(default=30, ge=1, le=1_000)

    background_jobs_enabled: bool = True
    sync_ingest_max_listings: int = Field(default=100, ge=1, le=5000)
    job_lease_seconds: int = Field(default=120, ge=30, le=3600)
    job_default_max_attempts: int = Field(default=3, ge=1, le=10)
    job_retry_base_seconds: int = Field(default=5, ge=1, le=3600)
    job_poll_seconds: float = Field(default=1.0, ge=0.1, le=60)

    max_csv_upload_bytes: int = 5 * 1024 * 1024
    cleaned_csv_retention_hours: int = Field(default=24, ge=1, le=720)
    max_cleaned_csv_exports: int = Field(default=50, ge=1, le=1000)

    max_scrape_response_bytes: int = 2 * 1024 * 1024
    scrape_timeout_seconds: float = 15.0
    max_scrape_redirects: int = 5
    scrape_allowed_domains: list[str] = Field(default_factory=list)
    browser_scraper_enabled: bool = False
    browser_scrape_allowed_domains: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
