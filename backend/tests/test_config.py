"""Tests for configuration loading."""

import os
from unittest.mock import patch

import pytest


class TestSettings:
    """Test settings configuration loading."""

    def test_settings_loads_from_environment(self) -> None:
        """Settings should load required values from environment variables."""
        env = {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/monzo",
            "MONZO_CLIENT_ID": "test-client-id",
            "MONZO_CLIENT_SECRET": "test-client-secret",
            "MONZO_REDIRECT_URI": "http://localhost:8000/auth/callback",
            "SECRET_KEY": "test-secret-key",
        }
        with patch.dict(os.environ, env, clear=True):
            from app.config import Settings

            settings = Settings()

            assert settings.database_url == env["DATABASE_URL"]
            assert settings.monzo_client_id == env["MONZO_CLIENT_ID"]
            assert settings.monzo_client_secret == env["MONZO_CLIENT_SECRET"]
            assert settings.monzo_redirect_uri == env["MONZO_REDIRECT_URI"]
            assert settings.secret_key == env["SECRET_KEY"]

    def test_settings_has_default_sync_interval(self) -> None:
        """Settings should have a default sync interval of 24 hours."""
        env = {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/monzo",
            "MONZO_CLIENT_ID": "test-client-id",
            "MONZO_CLIENT_SECRET": "test-client-secret",
            "MONZO_REDIRECT_URI": "http://localhost:8000/auth/callback",
            "SECRET_KEY": "test-secret-key",
        }
        with patch.dict(os.environ, env, clear=True):
            from app.config import Settings

            settings = Settings()

            assert settings.sync_interval_hours == 24

    def test_settings_slack_webhook_optional(self) -> None:
        """Slack webhook URL should be optional."""
        env = {
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/monzo",
            "MONZO_CLIENT_ID": "test-client-id",
            "MONZO_CLIENT_SECRET": "test-client-secret",
            "MONZO_REDIRECT_URI": "http://localhost:8000/auth/callback",
            "SECRET_KEY": "test-secret-key",
        }
        with patch.dict(os.environ, env, clear=True):
            from app.config import Settings

            settings = Settings()

            assert settings.slack_webhook_url is None

    def test_settings_validates_required_fields(self) -> None:
        """Settings should fail validation when required fields are missing."""
        from pydantic import ValidationError

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                from app.config import Settings

                Settings()
