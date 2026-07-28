"""Application settings.

Single source of truth for configuration. Values come from environment
variables (or the .env file in local development). Every module (LLM
client, DB connectors, guardrails) reads its config from here — never
from os.environ directly. That keeps the Claude/Bedrock switch and
hackathon-day reconfiguration a one-line .env change.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_env: str = "local"
    app_name: str = "trusted-enterprise-agent"
    version: str = "0.1.0"

    # PII pseudonymization: HMAC key that fixes the original->fake mapping.
    # Rotate per environment; in production this lives in a KMS, not in .env.
    pii_secret_key: str = "change-me-before-the-event"

    # CORS: origins allowed to call the API (Angular dev server by default).
    cors_origins: list[str] = ["http://localhost:4200"]

    # Guardrails
    guardrails_use_llm: bool = False  # enable the LLM injection classifier layer

    # Agent data-access policy
    agent_denied_columns: list[str] = ["TELF1", "SMTP_ADDR"]  # restricted PII columns
    agent_max_rows: int = 500

    # Database
    database_url: str = "postgresql+psycopg://tea:tea@localhost:5432/tea"

    # LLM provider switch: anthropic | bedrock
    llm_provider: str = "anthropic"

    # Anthropic API (direct)
    anthropic_api_key: str = ""
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    llm_smart_model: str = "claude-sonnet-4-6"

    # AWS Bedrock (sponsor credits). Verify exact model IDs in the AWS
    # console on hackathon day — they vary by region and account.
    aws_region: str = "eu-central-1"
    bedrock_fast_model_id: str = "anthropic.claude-haiku-4-5-v1:0"
    bedrock_smart_model_id: str = "anthropic.claude-sonnet-4-6-v1:0"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — parsed once per process."""
    return Settings()
