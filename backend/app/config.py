"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str

    # Monzo OAuth
    monzo_client_id: str
    monzo_client_secret: str
    monzo_redirect_uri: str

    # Security
    secret_key: str

    # Sync configuration
    sync_interval_hours: int = 24

    # Slack (optional)
    slack_webhook_url: str | None = None
