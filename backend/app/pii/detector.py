"""Structured PII detection: emails, phone numbers, IBANs, person names.

Two engines behind one function:
- Presidio + spaCy NER for person names (statistical, catches names the
  fuzzy target-list search cannot — unknown people, not just our watch list);
- pure-regex for emails, phones, IBANs (deterministic, always available).

The regex layer always runs. The Presidio layer runs when its spaCy model
is installed; if the model is missing, detection degrades to regex-only
instead of crashing — CI and teammates without the model stay green. The
public result type is ours, not Presidio's, so swapping engines never
touches callers.

Model note: we pin the small model (en_core_web_sm, ~12 MB) explicitly
rather than relying on Presidio's default (en_core_web_lg, ~560 MB). The
small model's accuracy on person names is close, and the size difference
matters for the Docker image and CI. Install it with:
    python -m spacy download en_core_web_sm
"""

import re
from dataclasses import dataclass
from functools import lru_cache

from app.config import get_settings

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
    """Build the Presidio engine once with an explicit spaCy model.

    Returns None (not an exception) if Presidio or the model is unavailable,
    so callers degrade to regex-only detection gracefully.
    """
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        model = get_settings().presidio_spacy_model
        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": model}],
            }
        )
        return AnalyzerEngine(nlp_engine=provider.create_engine())
    except Exception:
        return None


def presidio_available() -> bool:
    """True when the NER engine is loaded — surfaced on the eval report."""
    return _presidio_analyzer() is not None


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
