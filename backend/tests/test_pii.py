"""Stage 3 verification: fuzzy matching, recall vs ground truth,
deterministic pseudonymization that keeps the data usable."""

import csv
import json

from app.data.synthetic import generate
from app.pii.fuzzy import score_cell, score_text
from app.pii.normalize import normalize
from app.pii.pseudonymize import Pseudonymizer
from app.pii.service import pseudonymize_dataset, scan

# ── Fuzzy matching unit checks ───────────────────────────────────────

def test_cell_matching_handles_legacy_spellings() -> None:
    for variant in ("Paul Jonas", "Jonas, Paul", "PAUL JONAS", "Paul Jnoas"):
        match = score_cell(variant, "Paul Jonas")
        assert match is not None and match.score >= 80, (variant, match)


def test_cell_matching_handles_initials() -> None:
    match = score_cell("P. Jonas", "Paul Jonas")
    assert match is not None and match.score >= 90
    assert match.method == "initials"


def test_cyrillic_transliteration_matches() -> None:
    match = score_cell("Юрий Ковалёв", "Yuri Kovalev")
    assert match is not None and match.score >= 75, match


def test_text_matching_finds_name_inside_sentence() -> None:
    match = score_text("Payment to Jonas, Paul re invoice 84551", "Paul Jonas")
    assert match is not None and match.score >= 80


def test_unrelated_names_do_not_match() -> None:
    match = score_cell("Andrea Bernasconi", "Paul Jonas")
    assert match is not None and match.score < 60


# ── Recall against the Stage 2 ground truth ──────────────────────────

TARGETS = ["Paul Jonas", "Paula Erickson", "Yuri Kovalev"]


def test_scan_recall_against_ground_truth(tmp_path) -> None:
    data_dir = generate(tmp_path / "data", seed=42)
    truth = json.loads((data_dir / "ground_truth.json").read_text())

    findings = scan(data_dir, TARGETS)
    found_locations = {(f.table, f.row_key, f.column) for f in findings}

    expected = [
        (o["table"], o["row_key"], o["column"])
        for e in truth["entities"]
        for o in e["occurrences"]
        if o["pii_type"] == "PERSON_NAME"
    ]
    hit = sum(1 for location in expected if location in found_locations)
    recall = hit / len(expected)
    assert recall >= 0.8, f"recall {recall:.2f} ({hit}/{len(expected)})"


def test_scan_finds_official_test_case_minimum(tmp_path) -> None:
    """The 2025 acceptance test: 'Paul Jonas' must return >= 3 results."""
    data_dir = generate(tmp_path / "data", seed=42)
    findings = scan(data_dir, ["Paul Jonas"])
    person_hits = [f for f in findings if f.matched_person == "Paul Jonas"]
    assert len(person_hits) >= 3


def test_scan_detects_emails_via_regex(tmp_path) -> None:
    data_dir = generate(tmp_path / "data", seed=42)
    findings = scan(data_dir, [])
    assert any(f.pii_type == "EMAIL" for f in findings)


# ── Deterministic pseudonymization ───────────────────────────────────

def test_pseudonymizer_is_deterministic_across_calls() -> None:
    first = Pseudonymizer("key-a").identity_for("Paul Jonas")
    second = Pseudonymizer("key-a").identity_for("paul jonas")  # spelling-insensitive
    assert first == second


def test_pseudonymizer_depends_on_secret_key() -> None:
    with_key_a = Pseudonymizer("key-a").identity_for("Paul Jonas")
    with_key_b = Pseudonymizer("key-b").identity_for("Paul Jonas")
    assert with_key_a != with_key_b


def test_replace_preserves_format() -> None:
    pseudonymizer = Pseudonymizer("key-a")
    identity = pseudonymizer.identity_for("Paul Jonas")

    comma_form = pseudonymizer.replace_name("Jonas, Paul", "Paul Jonas")
    assert comma_form == f"{identity['last']}, {identity['first']}"

    initial_form = pseudonymizer.replace_name("P. Jonas", "Paul Jonas")
    assert initial_form == f"{identity['first'][0]}. {identity['last']}"

    upper_form = pseudonymizer.replace_name("PAUL JONAS", "Paul Jonas")
    assert upper_form.isupper()


def test_pseudonymized_dataset_has_no_originals_and_intact_joins(tmp_path) -> None:
    data_dir = generate(tmp_path / "data", seed=42)
    out_dir = tmp_path / "clean"

    summary = pseudonymize_dataset(data_dir, out_dir, TARGETS)
    assert summary["replaced_cells"] > 0

    # 1. Original surnames must be gone from every output table.
    clean_text = " ".join(
        (out_dir / name).read_text() for name in ("kna1.csv", "lfa1.csv", "bseg.csv")
    )
    for surname in ("Jonas", "Erickson", "Kovalev", "Ковалёв"):
        assert surname not in clean_text, f"{surname} leaked into pseudonymized output"

    # 2. Joins survive: KUNNR keys are byte-identical before and after.
    def keys(path):
        with open(path, newline="") as handle:
            return [row["KUNNR"] for row in csv.DictReader(handle)]

    assert keys(data_dir / "kna1.csv") == keys(out_dir / "kna1.csv")

    # 3. One person -> one fake identity everywhere: the same fake surname
    #    appears in both kna1 and lfa1 for the same original person.
    vault = json.loads((out_dir / "pseudonym_vault.json").read_text())
    fake_last = vault[normalize("Paul Jonas")]["last"]
    assert fake_last in (out_dir / "kna1.csv").read_text()
    assert fake_last in (out_dir / "lfa1.csv").read_text()
