"""Output guardrail: no restricted PII leaves the system.

Reuses the Stage 3 detector (single source of truth for what PII is).
Scans the agent's final answer text; if a restricted PII type is present,
the answer is redacted before it reaches the user. This is layer 4 of the
architecture: even if every earlier layer failed, raw PII does not exit.
"""

from dataclasses import dataclass

from app.pii.detector import detect

# Types that must never appear in a user-facing answer. Person names are
# allowed in answers (the user asked about a vendor by name); contact PII
# and financial identifiers are not.
RESTRICTED_OUTPUT_TYPES = {"EMAIL", "PHONE", "IBAN"}


@dataclass
class OutputScan:
    safe: bool
    redacted_text: str
    found_types: list[str]


def inspect_output(text: str) -> OutputScan:
    entities = [
        entity
        for entity in detect(text, use_presidio=False)
        if entity.pii_type in RESTRICTED_OUTPUT_TYPES
    ]
    if not entities:
        return OutputScan(safe=True, redacted_text=text, found_types=[])

    # Redact from the end so earlier offsets stay valid.
    redacted = text
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        redacted = (
            redacted[: entity.start] + f"[REDACTED_{entity.pii_type}]" + redacted[entity.end :]
        )
    return OutputScan(
        safe=False,
        redacted_text=redacted,
        found_types=sorted({entity.pii_type for entity in entities}),
    )
