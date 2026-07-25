"""AWS Bedrock implementation (uses sponsor credits, Converse API).

Model IDs differ from Anthropic API model names and vary by region.
They are configured in .env; VERIFY the exact IDs in the AWS console
on hackathon day (Bedrock -> Model catalog -> copy inference profile ID).
"""

from __future__ import annotations

import time

import boto3

from app.config import get_settings
from app.llm.base import LLMClient, LLMResponse, ModelTier
from app.llm.meter import meter
from app.llm.pricing import estimate_cost_usd


class BedrockClient(LLMClient):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self._models = {
            ModelTier.FAST: settings.bedrock_fast_model_id,
            ModelTier.SMART: settings.bedrock_smart_model_id,
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

        kwargs: dict = {
            "modelId": model,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": max_tokens},
        }
        if system:
            kwargs["system"] = [{"text": system}]

        response = self._client.converse(**kwargs)

        latency_ms = int((time.perf_counter() - started) * 1000)
        text = "".join(
            part["text"] for part in response["output"]["message"]["content"] if "text" in part
        )
        usage = response["usage"]
        cost = estimate_cost_usd(model, usage["inputTokens"], usage["outputTokens"])
        meter.record(model, usage["inputTokens"], usage["outputTokens"], cost)

        return LLMResponse(
            text=text,
            model=model,
            input_tokens=usage["inputTokens"],
            output_tokens=usage["outputTokens"],
            cost_usd=cost,
            latency_ms=latency_ms,
        )
