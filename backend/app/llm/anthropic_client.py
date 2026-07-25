"""Anthropic API implementation (direct, uses the voucher / API key)."""

from __future__ import annotations

import time

from anthropic import Anthropic

from app.config import get_settings
from app.llm.base import LLMClient, LLMResponse, ModelTier
from app.llm.meter import meter
from app.llm.pricing import estimate_cost_usd


class AnthropicClient(LLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._models = {
            ModelTier.FAST: settings.llm_fast_model,
            ModelTier.SMART: settings.llm_smart_model,
        }

    def complete(
        self,
        prompt: str,
        *,
        tier: ModelTier = ModelTier.FAST,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        model = self._models[tier]
        started = time.perf_counter()

        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        text = "".join(block.text for block in response.content if block.type == "text")
        cost = estimate_cost_usd(model, response.usage.input_tokens, response.usage.output_tokens)
        meter.record(model, response.usage.input_tokens, response.usage.output_tokens, cost)

        return LLMResponse(
            text=text,
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
        )
