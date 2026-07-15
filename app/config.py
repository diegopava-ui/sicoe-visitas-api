from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SICOE VISITAS API"
    app_version: str = "1.0.0"
    environment: str = "production"

    db_host: str 
    db_port: int = 5432
    db_name: str 
    db_user: str 
    db_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()