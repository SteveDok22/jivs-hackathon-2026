"""Structured output: prompt -> validated Pydantic model.

Foundation for the agent (Stage 4: SQL plans) and the refactoring
pipeline (backup bet: GeneratedComponent). The LLM is asked for pure
JSON; the answer is validated against the schema; on failure we retry
once, feeding the validation error back to the model.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMClient, ModelTier

_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(text: str) -> str:
    """Strip markdown fences and anything outside the outermost JSON object."""
    cleaned = _JSON_FENCE.sub("", text).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        return cleaned[start : end + 1]
    return cleaned


def complete_structured[T: BaseModel](
    client: LLMClient,
    prompt: str,
    schema: type[T],
    *,
    tier: ModelTier = ModelTier.SMART,
    system: str | None = None,
    max_tokens: int = 2048,
) -> T:
    """Ask the LLM for JSON matching `schema`; validate; retry once on failure."""
    json_schema = json.dumps(schema.model_json_schema(), indent=2)
    base_system = (
        (system + "\n\n") if system else ""
    ) + (
        "Respond with a single JSON object only. No prose, no markdown fences.\n"
        f"The JSON must match this schema:\n{json_schema}"
    )

    last_error = ""
    current_prompt = prompt
    for _attempt in range(2):
        response = client.complete(
            current_prompt, tier=tier, system=base_system, max_tokens=max_tokens
        )
        try:
            return schema.model_validate_json(_extract_json(response.text))
        except (ValidationError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            current_prompt = (
                f"{prompt}\n\nYour previous answer failed validation:\n{last_error}\n"
                "Return corrected JSON only."
            )
    raise ValueError(f"Structured output failed after retry: {last_error}")
