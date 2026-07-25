"""Cost tracking for every LLM call.

Why this exists: the jury evaluation sheet scores measurable quality,
and our eval panel (Stage 6) shows "cost per 1000 records" live.
Every call goes through the meter, so the number is real, not estimated.

Prices are USD per million tokens (input, output).
VERIFY against current provider pricing right before the event —
prices change, and Bedrock IDs bill under their own names.
"""

from threading import Lock

from app.llm.schemas import Usage

# Keys are substrings: "haiku" matches "claude-haiku-4-5-20251001" and
# Bedrock IDs like "anthropic.claude-haiku-4-5-v1:0" alike.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "haiku": (1.00, 5.00),
    "sonnet": (3.00, 15.00),
}
DEFAULT_PRICE: tuple[float, float] = (3.00, 15.00)


def estimate_cost_usd(model: str, usage: Usage) -> float:
    # Bedrock IDs embed the API name (e.g. "eu.anthropic.claude-sonnet-4-6-v1:0"),
    # so substring matching maps them onto the same price row.
    price_in, price_out = DEFAULT_PRICE
    for known, (p_in, p_out) in PRICES_PER_MTOK.items():
        if known in model.lower():
            price_in, price_out = p_in, p_out
            break
    return (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000


class CostMeter:
    """Thread-safe in-memory accumulator. One instance per process."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with getattr(self, "_lock", Lock()):
            self.calls: int = 0
            self.input_tokens: int = 0
            self.output_tokens: int = 0
            self.cost_usd: float = 0.0
            self.by_model: dict[str, dict[str, float]] = {}

    def record(self, model: str, usage: Usage) -> None:
        cost = estimate_cost_usd(model, usage)
        with self._lock:
            self.calls += 1
            self.input_tokens += usage.input_tokens
            self.output_tokens += usage.output_tokens
            self.cost_usd += cost
            row = self.by_model.setdefault(
                model, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
            )
            row["calls"] += 1
            row["input_tokens"] += usage.input_tokens
            row["output_tokens"] += usage.output_tokens
            row["cost_usd"] += cost

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "calls": self.calls,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_usd": round(self.cost_usd, 6),
                "by_model": {m: {**row, "cost_usd": round(row["cost_usd"], 6)}
                             for m, row in self.by_model.items()},
            }


_meter = CostMeter()


def get_meter() -> CostMeter:
    return _meter
