"""LLM providers behind one interface.

Three implementations:
- AnthropicProvider: direct Claude API (the CHF 150 voucher scenario)
- BedrockProvider:   AWS Bedrock via the converse API (the AWS credits scenario)
- FakeProvider:      deterministic, offline — powers our tests and lets the
                     whole pipeline run without keys or network

Switching provider is a .env change (LLM_PROVIDER), zero code edits.
"""

from typing import Protocol

from app.llm.schemas import LLMResult, Usage


class Provider(Protocol):
    def complete(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        max_tokens: int,
        cache_system: bool,
    ) -> LLMResult: ...


class AnthropicProvider:
    def __init__(self, api_key: str) -> None:
        import anthropic  # lazy import: tests never need the SDK

        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        max_tokens: int,
        cache_system: bool,
    ) -> LLMResult:
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            if cache_system:
                # Prompt caching: a large stable system prompt (e.g. the DB schema
                # catalog in Stage 4) is billed at the cached rate on repeat calls.
                kwargs["system"] = [
                    {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
                ]
            else:
                kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResult(
            text=text,
            model=model,
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
        )


class BedrockProvider:
    def __init__(self, region: str) -> None:
        import boto3  # lazy import

        self._client = boto3.client("bedrock-runtime", region_name=region)

    def complete(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        max_tokens: int,
        cache_system: bool,  # noqa: ARG002 — caching config differs on Bedrock; TODO on-site
    ) -> LLMResult:
        kwargs: dict = {
            "modelId": model,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": max_tokens},
        }
        if system:
            kwargs["system"] = [{"text": system}]
        response = self._client.converse(**kwargs)
        parts = response["output"]["message"]["content"]
        text = "".join(p.get("text", "") for p in parts)
        usage = response.get("usage", {})
        return LLMResult(
            text=text,
            model=model,
            usage=Usage(
                input_tokens=usage.get("inputTokens", 0),
                output_tokens=usage.get("outputTokens", 0),
            ),
        )


class FakeProvider:
    """Returns scripted responses in order. Deterministic and offline."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = list(responses or ["fake response"])
        self.calls: list[dict] = []

    def complete(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        max_tokens: int,
        cache_system: bool,
    ) -> LLMResult:
        self.calls.append(
            {
                "model": model,
                "system": system,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "cache_system": cache_system,
            }
        )
        index = min(len(self.calls) - 1, len(self._responses) - 1)
        return LLMResult(
            text=self._responses[index],
            model=model,
            usage=Usage(input_tokens=10, output_tokens=20),
        )
