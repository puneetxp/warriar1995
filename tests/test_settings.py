"""
tests/test_settings.py

Tests for dynamic configuration reloading and type casting.
"""

import os
import pytest
from security.settings import get_settings, reload_settings_from_env


def test_reload_settings_from_env_dict():
    """Verify reload_settings_from_env correctly updates settings from a dict."""
    settings = get_settings()
    
    # Save original values
    orig_env = settings.APP_ENV
    orig_key = settings.ANTHROPIC_API_KEY
    orig_calls = settings.RATE_LIMIT_CALLS
    orig_origins = settings.ALLOWED_ORIGINS
    
    try:
        # Create a mock env dictionary with updated configuration values
        mock_env = {
            "APP_ENV": "production",
            "ANTHROPIC_API_KEY": "sk-ant-test-key-123456789",
            "RATE_LIMIT_CALLS": "50",
            "ALLOWED_ORIGINS": "https://example.com,https://api.example.com",
            "DEBUG": "true",
            "LLM_DEFAULT_TEMPERATURE": "0.7",
        }
        
        # Reload settings
        updated = reload_settings_from_env(mock_env)
        
        # Verify the returned object is the same singleton
        assert updated is settings
        
        # Verify fields were updated and cast to the correct type
        assert settings.APP_ENV == "production"
        assert settings.ANTHROPIC_API_KEY == "sk-ant-test-key-123456789"
        assert settings.RATE_LIMIT_CALLS == 50
        assert settings.ALLOWED_ORIGINS == ["https://example.com", "https://api.example.com"]
        assert settings.DEBUG is True
        assert settings.LLM_DEFAULT_TEMPERATURE == 0.7
        
        # Verify values were set in os.environ
        assert os.environ.get("APP_ENV") == "production"
        assert os.environ.get("ANTHROPIC_API_KEY") == "sk-ant-test-key-123456789"
        assert os.environ.get("RATE_LIMIT_CALLS") == "50"
        
    finally:
        # Restore original values to prevent affecting other tests
        restore_env = {
            "APP_ENV": orig_env,
            "ANTHROPIC_API_KEY": orig_key,
            "RATE_LIMIT_CALLS": str(orig_calls),
            "ALLOWED_ORIGINS": ",".join(orig_origins),
            "DEBUG": "false",
            "LLM_DEFAULT_TEMPERATURE": "0.4",
        }
        reload_settings_from_env(restore_env)


def test_reload_settings_from_env_json_list():
    """Verify reload_settings_from_env handles JSON-formatted lists."""
    settings = get_settings()
    orig_origins = settings.ALLOWED_ORIGINS
    
    try:
        mock_env = {
            "ALLOWED_ORIGINS": '["http://localhost:3000", "http://localhost:8000"]'
        }
        reload_settings_from_env(mock_env)
        assert settings.ALLOWED_ORIGINS == ["http://localhost:3000", "http://localhost:8000"]
    finally:
        reload_settings_from_env({"ALLOWED_ORIGINS": ",".join(orig_origins)})


class MockCloudflareEnv:
    """Mock class representing Cloudflare Workers self.env bindings object."""
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)


def test_reload_settings_from_cf_object():
    """Verify reload_settings_from_env works with Cloudflare Workers env objects (non-dict)."""
    settings = get_settings()
    orig_env = settings.APP_ENV
    
    try:
        cf_env = MockCloudflareEnv({
            "APP_ENV": "staging",
            "DEBUG": "1"
        })
        
        reload_settings_from_env(cf_env)
        assert settings.APP_ENV == "staging"
        assert settings.DEBUG is True
    finally:
        reload_settings_from_env({"APP_ENV": orig_env, "DEBUG": "false"})
