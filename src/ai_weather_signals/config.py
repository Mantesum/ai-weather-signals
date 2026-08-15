from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://weather_signals:change-me@127.0.0.1:5433/weather_signals"
    source_config_path: Path = Path("config/sources.yaml")
    city_config_path: Path = Path("config/cities.yaml")
    confidence_config_path: Path = Path("config/confidence.yaml")
    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_model: str = "Qwen3-8B-Q4_K_M.gguf"
    llm_api_key: str = ""
    llm_enabled: bool = True
    author_hash_salt: str = Field(default="development-only-change-me", min_length=8)
    log_level: str = "INFO"
    raw_text_retention_days: int = Field(default=30, ge=0)
    schema_version: str = "1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
