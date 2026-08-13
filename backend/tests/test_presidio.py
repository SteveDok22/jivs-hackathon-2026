"""Stage 11 verification: Presidio NER detection and discovery.

These tests need the spaCy model (en_core_web_sm). When it is absent they
skip rather than fail, so CI without the model stays green — the detector's
graceful-degradation contract is itself tested separately below.
"""

import pytest

from app.data.synthetic import generate
from app.pii.detector import detect, presidio_available
from app.pii.service import discover_persons, scan

needs_presidio = pytest.mark.skipif(
    not presidio_available(), reason="spaCy model en_core_web_sm not installed"
)


def test_regex_layer_always_works_without_presidio() -> None:
    # Emails are regex-detected regardless of the NER engine.
    entities = detect("Reach me at anna.meier@example.com", use_presidio=False)
    assert any(e.pii_type == "EMAIL" and e.engine == "regex" for e in entities)


@needs_presidio
def test_presidio_detects_person_names() -> None:
    entities = detect("Payment to Paul Jonas for invoice 84551", use_presidio=True)
    persons = [e for e in entities if e.pii_type == "PERSON_NAME"]
    assert persons and persons[0].engine == "presidio"
    assert "Jonas" in persons[0].value


@needs_presidio
def test_presidio_ignores_non_names() -> None:
    entities = detect("Monthly service fee", use_presidio=True)
    assert not [e for e in entities if e.pii_type == "PERSON_NAME"]


@needs_presidio
def test_discovery_finds_more_than_the_watchlist(tmp_path) -> None:
    """The core value of NER: find people we did NOT search for."""
    data_dir = generate(tmp_path, seed=42)

    watchlist = {
        f.matched_person for f in scan(data_dir, ["Paul Jonas"])
        if f.pii_type == "PERSON_NAME"
    }
    discovered = {f.value for f in discover_persons(data_dir)}

    # Discovery must find far more distinct people than a 1-name watch-list.
    assert len(discovered) > len(watchlist) + 20
    # And it still includes the watch-listed person.
    assert any("Jonas" in name for name in discovered)


def test_customer_id_not_flagged_as_phone() -> None:
    """A bare digit run (customer number) must not be detected as a phone."""
    entities = detect("customer number 0000001063", use_presidio=False)
    assert not [e for e in entities if e.pii_type == "PHONE"]


def test_real_phone_still_detected() -> None:
    """Phones with separators or + prefix are still caught."""
    for text in ["+41 44 123 45 67", "call 079 555 12 34"]:
        entities = detect(text, use_presidio=False)
        assert [e for e in entities if e.pii_type == "PHONE"], text
