from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)

    database_url: str = Field(repr=False)
    supabase_url: str
    supabase_jwt_audience: str = "authenticated"
    cors_origins: str

    @field_validator("database_url")
    @classmethod
    def check_database(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"postgresql", "postgres", "postgresql+psycopg"} or not parsed.hostname:
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return value

    @field_validator("supabase_url")
    @classmethod
    def check_supabase(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path not in {"", "/"}:
            raise ValueError("SUPABASE_URL must be a project HTTPS origin")
        return value.rstrip("/")

    @property
    def allowed_origins(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins or any(urlparse(origin).scheme != "https" for origin in origins):
            raise ValueError("CORS_ORIGINS must contain HTTPS origins")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
