from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketSense NG API"
    app_version: str = "0.3.0"
    database_url: str = "sqlite+aiosqlite:///./marketsense.db"
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    sql_echo: bool = False

    max_csv_upload_bytes: int = 5 * 1024 * 1024
    max_scrape_response_bytes: int = 2 * 1024 * 1024
    scrape_timeout_seconds: float = 15.0
    max_scrape_redirects: int = 5
    scrape_allowed_domains: list[str] = Field(default_factory=list)

    browser_scraper_enabled: bool = False
    browser_scrape_allowed_domains: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
