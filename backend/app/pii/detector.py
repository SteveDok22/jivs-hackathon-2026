"""Structured PII detection: emails, phone numbers, IBANs, person names.

Two engines behind one function:
- Presidio + spaCy NER when installed (full power, used at the event);
- pure-regex fallback (emails, phones, IBANs) that always works — CI and
  teammates without the spaCy model stay green.

The public result type is ours, not Presidio's, so swapping engines
never touches callers.
"""

import re
from dataclasses import dataclass
from functools import lru_cache

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"(?:\+?\d[\d\s()/-]{7,}\d)")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b")


@dataclass
class PIIEntity:
    pii_type: str      # EMAIL | PHONE | IBAN | PERSON_NAME
    value: str
    start: int
    end: int
    score: float
    engine: str        # "regex" | "presidio"


@lru_cache
def _presidio_analyzer():
    """Build the Presidio engine once, or return None if unavailable."""
    try:
        from presidio_analyzer import AnalyzerEngine

        return AnalyzerEngine()
    except Exception:
        return None


def detect(text: str, *, use_presidio: bool = True) -> list[PIIEntity]:
    entities: list[PIIEntity] = []

    for pattern, pii_type in ((_EMAIL, "EMAIL"), (_PHONE, "PHONE"), (_IBAN, "IBAN")):
        for match in pattern.finditer(text):
            entities.append(
                PIIEntity(
                    pii_type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    score=0.9,
                    engine="regex",
                )
            )

    analyzer = _presidio_analyzer() if use_presidio else None
    if analyzer is not None:
        for result in analyzer.analyze(text=text, language="en", entities=["PERSON"]):
            entities.append(
                PIIEntity(
                    pii_type="PERSON_NAME",
                    value=text[result.start : result.end],
                    start=result.start,
                    end=result.end,
                    score=result.score,
                    engine="presidio",
                )
            )
    return entities
