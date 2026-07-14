from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SICOE VISITAS API"
    app_version: str = "1.0.0"
    environment: str = "development"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "sicoe_visitas"
    db_user: str = "sicoe_user"
    db_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()