"""
Application configuration.

Loads and validates environment variables required by the
AI Pull Request Code Reviewer.

A `.env` file is supported for local development.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    """Validated application configuration."""

    # ------------------------------------------------------------------
    # AI provider
    # ------------------------------------------------------------------

    # Determines which model provider the application should use.
    # Supported values: "openai" or "deepseek".
    model_provider: Literal["openai", "deepseek"] = Field(
        default="openai",
        validation_alias="MODEL_PROVIDER",
    )

    # ------------------------------------------------------------------
    # OpenAI configuration
    # ------------------------------------------------------------------

    # API key used when MODEL_PROVIDER=openai.
    openai_api_key: str = Field(
        ...,
        validation_alias="OPENAI_API_KEY",
    )

    # OpenAI model used for code reviews.
    openai_model_name: str = Field(
        default="gpt-5.4-mini",
        validation_alias="OPENAI_MODEL_NAME",
    )

    # ------------------------------------------------------------------
    # DeepSeek configuration
    # ------------------------------------------------------------------

    # API key used when MODEL_PROVIDER=deepseek.
    deepseek_api_key: str = Field(
        ...,
        validation_alias="DEEPSEEK_API_KEY",
    )

    # DeepSeek model used for code reviews.
    deepseek_model_name: str = Field(
        default="deepseek-flash",
        validation_alias="DEEPSEEK_MODEL_NAME",
    )

    # DeepSeek exposes an OpenAI-compatible API.
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        validation_alias="DEEPSEEK_BASE_URL",
    )

    # ------------------------------------------------------------------
    # GitHub configuration
    # ------------------------------------------------------------------

    # GitHub token used to read pull-request information and
    # post review comments.
    github_token: str = Field(
        ...,
        validation_alias="GITHUB_TOKEN",
    )

    # Secret used to verify that incoming webhook requests
    # genuinely originate from GitHub.
    github_webhook_secret: str = Field(
        ...,
        validation_alias="GITHUB_WEBHOOK_SECRET",
    )

    # ------------------------------------------------------------------
    # Application configuration
    # ------------------------------------------------------------------

    # Maximum amount of diff text that can be sent to the AI model.
    max_diff_chars: int = Field(
        default=300_000,
        gt=0,
        validation_alias="MAX_DIFF_CHARS",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Create and cache the application settings.

    Returns:
        A validated Settings instance.
    """
    return Settings()


# Shared settings instance used throughout the application.
settings = get_settings()


if __name__ == "__main__":
    print("Environment file:", ENV_FILE)
    print("Environment file exists:", ENV_FILE.exists())

    print("\nConfiguration loaded successfully:")
    print("Model provider:", settings.model_provider)
    print("OpenAI model:", settings.openai_model_name)
    print("DeepSeek model:", settings.deepseek_model_name)
    print("DeepSeek base URL:", settings.deepseek_base_url)
    print("Max diff chars:", settings.max_diff_chars)

    print("\nSecrets loaded:")
    print("OpenAI API key:", bool(settings.openai_api_key))
    print("DeepSeek API key:", bool(settings.deepseek_api_key))
    print("GitHub token:", bool(settings.github_token))
    print("GitHub webhook secret:", bool(settings.github_webhook_secret))