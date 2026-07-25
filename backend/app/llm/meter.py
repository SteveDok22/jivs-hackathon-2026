"""Cost meter — accumulates usage across the whole process.

Feeds the eval dashboard (Stage 6) and answers the question the team
must know at all times during the 24h: "how much voucher is left?"
Thread-safe because FastAPI handles requests concurrently.
"""

from __future__ import annotations

import threading

from pydantic import BaseModel


class UsageSummary(BaseModel):
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    by_model: dict[str, float] = {}


class CostMeter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._summary = UsageSummary()

    def record(self, model: str, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        with self._lock:
            s = self._summary
            s.calls += 1
            s.input_tokens += input_tokens
            s.output_tokens += output_tokens
            s.cost_usd = round(s.cost_usd + cost_usd, 6)
            s.by_model[model] = round(s.by_model.get(model, 0.0) + cost_usd, 6)

    def summary(self) -> UsageSummary:
        with self._lock:
            return self._summary.model_copy(deep=True)

    def reset(self) -> None:
        with self._lock:
            self._summary = UsageSummary()


# Process-wide singleton: every client instance reports here.
meter = CostMeter()
