"""Centralized application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # SQLite is used by default for local development and the current MVP stage.
    database_url: str = "sqlite:///./portfolio.db"
    # A single password is enough because the site has only one admin user.
    admin_password: str = "change-me"
    # SessionMiddleware signs the session cookie with this key.
    secret_key: str = "change-this-secret-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
