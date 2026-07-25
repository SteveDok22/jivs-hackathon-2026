"""Model pricing table (USD per million tokens).

Used to convert token usage into money so the live dashboard can show
"cost per 1000 records" — a jury-facing metric. Prices change; verify
against the provider pricing page right before the event and adjust
here — nothing else in the codebase touches prices.
"""

from __future__ import annotations

# model name substring -> (input $/MTok, output $/MTok)
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "haiku": (1.00, 5.00),
    "sonnet": (3.00, 15.00),
}

_DEFAULT = (3.00, 15.00)  # unknown model: assume smart-tier prices


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated cost in USD for a single call."""
    model_lower = model.lower()
    input_price, output_price = _DEFAULT
    for key, prices in PRICES_PER_MTOK.items():
        if key in model_lower:
            input_price, output_price = prices
            break
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
