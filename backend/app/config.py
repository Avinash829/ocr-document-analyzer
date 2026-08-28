from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    allowed_origins: str = "http://localhost:3000"
    max_file_size_mb: int = Field(default=25, ge=1, le=200)
    max_pages: int = Field(default=30, ge=1, le=200)
    max_image_dimension: int = Field(default=12000, ge=1000)
    processing_timeout_seconds: int = Field(default=600, ge=30)
    job_ttl_seconds: int = Field(default=3600, ge=300)
    ambiguous_threshold: float = Field(default=.68, ge=0, le=1)
    gemini_model: str = "gemini-3.7-flash"
    gemini_fallback_models: list[str] = ["gemini-3.6-flash", "gemini-3.5-flash"]
    gemini_max_attempts: int = Field(default=3, ge=1, le=10)
    gemini_timeout_seconds: int = Field(default=180, ge=5)
    gemini_key_cooldown_seconds: int = Field(default=120, ge=10)

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

