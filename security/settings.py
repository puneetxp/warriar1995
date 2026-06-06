"""
config/settings.py

Centralized configuration management using pydantic-settings.
All secrets come from environment variables — never hardcoded.
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Mental Wellness Tracker"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # ── Security ──────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    # NOTE: Wildcard is intentional for demo/development. In production, restrict
    # to specific domains e.g. ["https://your-frontend.com"]
    ALLOWED_ORIGINS: List[str] = ["*"]
    MAX_NOTE_LENGTH: int = 500
    MAX_JOURNAL_LENGTH: int = 2000
    MAX_TEXT_LENGTH: int = 3000

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_CALLS: int = 30        # requests
    RATE_LIMIT_PERIOD: int = 60       # seconds
    RATE_LIMIT_BURST: int = 10        # burst allowance

    # ── LLM ───────────────────────────────────────────────────────────────────
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_MAX_TOKENS: int = 1024
    LLM_DEFAULT_TEMPERATURE: float = 0.4
    LLM_TIMEOUT_SECONDS: int = 30

    # ── Cache ─────────────────────────────────────────────────────────────────
    CACHE_TTL_SECONDS: int = 300      # 5 minutes

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def api_key_configured(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY and len(self.ANTHROPIC_API_KEY) > 10)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
