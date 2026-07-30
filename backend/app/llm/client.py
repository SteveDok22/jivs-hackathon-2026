"""High-level LLM client used by every module in the project.

Rules encoded here (agreed team policy):
1. Model cascade — Tier.FAST (Haiku) for classification, filters, routing;
   Tier.SMART (Sonnet) for SQL generation and final answers. Never hardcode
   a model name anywhere else in the codebase: always ask by tier.
2. Every call is metered — tokens and USD land in the CostMeter,
   exposed at /llm/usage and later on the eval panel.
3. Structured output — `structured()` returns a validated Pydantic object,
   with one automatic retry that feeds the validation error back to the model.
"""

import json
import re
from enum import StrEnum
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.llm.cost import get_meter
from app.llm.providers import AnthropicProvider, BedrockProvider, Provider
from app.llm.schemas import LLMResult

T = TypeVar("T", bound=BaseModel)

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class Tier(StrEnum):
    FAST = "fast"
    SMART = "smart"


def _extract_json(text: str) -> str:
    """Models sometimes wrap JSON in markdown fences — strip them."""
    match = _JSON_FENCE.search(text)
    return match.group(1) if match else text.strip()


class LLMClient:
    def __init__(self, provider: Provider | None = None) -> None:
        settings = get_settings()
        # Model IDs are per-provider: switching LLM_PROVIDER in .env
        # automatically switches the whole cascade, no other edits.
        if settings.llm_provider == "bedrock":
            self._models = {
                Tier.FAST: settings.bedrock_fast_model_id,
                Tier.SMART: settings.bedrock_smart_model_id,
            }
        else:
            self._models = {
                Tier.FAST: settings.llm_fast_model,
                Tier.SMART: settings.llm_smart_model,
            }
        if provider is not None:
            self._provider: Provider = provider
        elif settings.llm_provider == "bedrock":
            self._provider = BedrockProvider(region=settings.aws_region)
        else:
            self._provider = AnthropicProvider(api_key=settings.anthropic_api_key)

    def complete(
        self,
        prompt: str,
        *,
        tier: Tier = Tier.FAST,
        system: str = "",
        max_tokens: int = 1024,
        cache_system: bool = False,
        image_b64: str | None = None,
    ) -> LLMResult:
        model = self._models[tier]
        result = self._provider.complete(
            model=model,
            system=system,
            prompt=prompt,
            max_tokens=max_tokens,
            cache_system=cache_system,
            image_b64=image_b64,
        )
        get_meter().record(model, result.usage)
        return result

    def structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        tier: Tier = Tier.SMART,
        system: str = "",
        max_tokens: int = 2048,
        image_b64: str | None = None,
    ) -> T:
        """Ask for JSON matching `schema`; validate; retry once on failure."""
        json_schema = json.dumps(schema.model_json_schema(), indent=2)
        instruction = (
            f"{prompt}\n\n"
            "Respond with a single JSON object matching this JSON Schema. "
            "No prose, no markdown fences, JSON only.\n"
            f"{json_schema}"
        )
        result = self.complete(
            instruction, tier=tier, system=system, max_tokens=max_tokens,
            image_b64=image_b64,
        )
        try:
            return schema.model_validate_json(_extract_json(result.text))
        except ValidationError as error:
            retry_prompt = (
                f"{instruction}\n\n"
                f"Your previous response was invalid:\n{result.text}\n\n"
                f"Validation errors:\n{error}\n\n"
                "Return corrected JSON only."
            )
            retry = self.complete(
                retry_prompt, tier=tier, system=system, max_tokens=max_tokens
            )
            return schema.model_validate_json(_extract_json(retry.text))


@lru_cache
def get_llm_client() -> LLMClient:
    """Process-wide client instance for routes and services."""
    return LLMClient()
