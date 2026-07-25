"""LLM abstraction layer.

Every part of the system (agent, guardrails, refactoring pipeline) talks
to this interface, never to a provider SDK directly. Swapping Anthropic
API for AWS Bedrock on hackathon day is a one-line .env change:
    LLM_PROVIDER=anthropic  ->  LLM_PROVIDER=bedrock
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel


class ModelTier(StrEnum):
    """Model cascade — the voucher burn-rate control.

    FAST  (Haiku):  classification, filters, routing, PII pre-checks.
    SMART (Sonnet): SQL generation, final answers, code generation.

    Rule of thumb: if the call happens inside a loop, it must be FAST.
    """

    FAST = "fast"
    SMART = "smart"


class LLMResponse(BaseModel):
    """Normalized response — identical shape for every provider."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


class LLMClient(ABC):
    """Provider-agnostic contract."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        tier: ModelTier = ModelTier.FAST,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a prompt, return normalized response with usage & cost."""
