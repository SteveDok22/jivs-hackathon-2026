"""Stage 1 verification: cascade, cost metering, structured output with retry.

All tests run on FakeProvider — offline, no keys, deterministic.
"""

from pydantic import BaseModel

from app.config import get_settings
from app.llm.client import LLMClient, Tier
from app.llm.cost import get_meter
from app.llm.providers import FakeProvider


def setup_function() -> None:
    get_meter().reset()


def test_cascade_selects_model_by_tier() -> None:
    provider = FakeProvider()
    client = LLMClient(provider=provider)

    fast = client.complete("classify this", tier=Tier.FAST)
    smart = client.complete("write sql", tier=Tier.SMART)

    settings = get_settings()
    assert fast.model == settings.llm_fast_model
    assert smart.model == settings.llm_smart_model


def test_every_call_is_metered() -> None:
    client = LLMClient(provider=FakeProvider())
    client.complete("one")
    client.complete("two", tier=Tier.SMART)

    snapshot = get_meter().snapshot()
    assert snapshot["calls"] == 2
    assert snapshot["input_tokens"] == 20
    assert snapshot["output_tokens"] == 40
    assert snapshot["cost_usd"] > 0
    settings = get_settings()
    assert set(snapshot["by_model"]) == {settings.llm_fast_model, settings.llm_smart_model}


class Invoice(BaseModel):
    vendor: str
    amount_chf: float


def test_structured_output_parses_valid_json() -> None:
    provider = FakeProvider(responses=['{"vendor": "Muller AG", "amount_chf": 4200.5}'])
    client = LLMClient(provider=provider)

    invoice = client.structured("extract the invoice", Invoice)

    assert invoice.vendor == "Muller AG"
    assert invoice.amount_chf == 4200.5


def test_structured_output_strips_markdown_fences() -> None:
    provider = FakeProvider(
        responses=['```json\n{"vendor": "Muller AG", "amount_chf": 1.0}\n```']
    )
    client = LLMClient(provider=provider)

    invoice = client.structured("extract", Invoice)

    assert invoice.vendor == "Muller AG"


def test_structured_output_retries_once_on_invalid_response() -> None:
    provider = FakeProvider(
        responses=[
            "sorry, I cannot produce JSON",                     # first attempt: invalid
            '{"vendor": "Muller AG", "amount_chf": 99.0}',      # retry: valid
        ]
    )
    client = LLMClient(provider=provider)

    invoice = client.structured("extract", Invoice)

    assert invoice.amount_chf == 99.0
    assert len(provider.calls) == 2
    # The retry prompt must include the validation error so the model can fix it.
    assert "Validation errors" in provider.calls[1]["prompt"]
