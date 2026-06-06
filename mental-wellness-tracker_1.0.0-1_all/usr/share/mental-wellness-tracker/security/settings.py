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


import os


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()


def reload_settings_from_env(env_obj) -> Settings:
    """Update settings in place using keys from an environment object or dict."""
    settings = get_settings()
    
    if env_obj is not None:
        keys = env_obj.keys() if isinstance(env_obj, dict) else dir(env_obj)
        for key in keys:
            if key.startswith("_"):
                continue
            val = env_obj[key] if isinstance(env_obj, dict) else getattr(env_obj, key)
            if hasattr(settings, key):
                field_type = type(settings).model_fields[key].annotation
                try:
                    # Handle basic conversions (e.g. lists, bools)
                    if field_type == bool:
                        if isinstance(val, str):
                            casted_val = val.lower() in ("true", "1", "yes")
                        else:
                            casted_val = bool(val)
                    elif field_type == list or getattr(field_type, "__origin__", None) == list:
                        if isinstance(val, str):
                            val_str = val.strip()
                            if val_str.startswith("[") and val_str.endswith("]"):
                                import json
                                casted_val = json.loads(val_str)
                            else:
                                casted_val = [item.strip() for item in val_str.split(",") if item.strip()]
                        else:
                            casted_val = list(val)
                    elif field_type == int:
                        casted_val = int(val)
                    elif field_type == float:
                        casted_val = float(val)
                    else:
                        casted_val = str(val)
                    setattr(settings, key, casted_val)
                except Exception:
                    setattr(settings, key, val)
                
                # Also set in os.environ so other libraries (like langchain) can read it
                os.environ[key] = str(val)
            elif key == "ANTHROPIC_API_KEY":
                # Ensure ANTHROPIC_API_KEY is placed in os.environ even if not explicitly defined on settings
                os.environ[key] = str(val)
    return settings

