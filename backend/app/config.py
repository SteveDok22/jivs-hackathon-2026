"""Application settings.

Single source of truth for configuration. Values come from environment
variables (or the .env file in local development). Every future module
(LLM client, DB connectors, guardrails) reads its config from here —
never from os.environ directly. That keeps the Claude/Bedrock switch
and hackathon-day reconfiguration a one-line .env change.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_env: str = "local"
    app_name: str = "trusted-enterprise-agent"
    version: str = "0.1.0"

    # Database
    database_url: str = "postgresql+psycopg://tea:tea@localhost:5432/tea"

    # LLM (used from Stage 1 onward)
    llm_provider: str = "anthropic"  # anthropic | bedrock
    anthropic_api_key: str = ""
    aws_region: str = "eu-central-1"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — parsed once per process."""
    return Settings()
