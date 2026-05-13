from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketSense NG API"
    app_version: str = "0.2.0"
    database_url: str = "sqlite+aiosqlite:///./marketsense.db"
    allowed_origins: list[str] = ["http://localhost:3000"]
    sql_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
