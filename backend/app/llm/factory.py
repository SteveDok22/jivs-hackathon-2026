"""Provider selection — the single switch point.

    LLM_PROVIDER=anthropic  -> direct Anthropic API (voucher)
    LLM_PROVIDER=bedrock    -> AWS Bedrock (sponsor credits)
"""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.llm.base import LLMClient


@lru_cache
def get_llm_client() -> LLMClient:
    provider = get_settings().llm_provider.lower()
    if provider == "anthropic":
        from app.llm.anthropic_client import AnthropicClient

        return AnthropicClient()
    if provider == "bedrock":
        from app.llm.bedrock_client import BedrockClient

        return BedrockClient()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'anthropic' or 'bedrock')")
