"""Application configuration.

Values are read from the environment so the same image runs locally (SQLite)
and in production (Postgres + Redis). See ``.env.example`` for the full list.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FC Edge API"
    environment: str = Field(default="development")

    # A SQLite default means the API boots with zero external services, which
    # keeps first-run and CI friction low. Production sets a Postgres DSN.
    database_url: str = Field(default="sqlite:///./fcedge.db")

    redis_url: str = Field(default="redis://localhost:6379/0")

    # Comma separated list of allowed CORS origins.
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    # Optional – enables the LLM-backed AI Coach. When unset we fall back to the
    # deterministic heuristic engine so the product is fully functional offline.
    openai_api_key: str | None = Field(default=None)

    # Live market ticker. In dev the API ticks in-process; in production Celery
    # beat drives ticks and this can be disabled on the web workers.
    enable_ticker: bool = Field(default=True)
    tick_interval_seconds: float = Field(default=5.0)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
