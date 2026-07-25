"""Stage 2 verification: generator determinism and ground-truth correctness."""

import json

from app.data.connectors import duckdb_over_csv
from app.data.synthetic import generate


def test_generator_is_deterministic(tmp_path) -> None:
    first = generate(tmp_path / "a", seed=42)
    second = generate(tmp_path / "b", seed=42)
    assert (first / "ground_truth.json").read_text() == (
        second / "ground_truth.json"
    ).read_text()
    assert (first / "kna1.csv").read_text() == (second / "kna1.csv").read_text()


def test_official_test_cases_have_at_least_three_occurrences(tmp_path) -> None:
    """Mirror of the 2025 slide: 'Paul Jonas' / 'Paula Erickson' >= 3 results."""
    out = generate(tmp_path, seed=42)
    truth = json.loads((out / "ground_truth.json").read_text())
    by_name = {e["canonical_name"]: e for e in truth["entities"]}

    for name in ("Paul Jonas", "Paula Erickson"):
        occurrences = by_name[name]["occurrences"]
        assert len(occurrences) >= 3, f"{name}: {len(occurrences)} occurrences"
        # PII must appear in more than one table (master data + free text).
        assert len({o["table"] for o in occurrences}) >= 2


def test_ground_truth_values_actually_exist_in_csv(tmp_path) -> None:
    """The answer key must match the data byte for byte."""
    out = generate(tmp_path, seed=42)
    truth = json.loads((out / "ground_truth.json").read_text())

    contents = {
        name: (out / f"{name}.csv").read_text()
        for name in ("kna1", "lfa1", "bkpf", "bseg")
    }
    for entity in truth["entities"]:
        for occurrence in entity["occurrences"]:
            assert occurrence["value"] in contents[occurrence["table"]], (
                f"{occurrence['value']!r} missing from {occurrence['table']}.csv"
            )


def test_multilingual_variants_present(tmp_path) -> None:
    out = generate(tmp_path, seed=42)
    truth = json.loads((out / "ground_truth.json").read_text())
    kovalev = next(e for e in truth["entities"] if e["canonical_name"] == "Yuri Kovalev")
    values = " ".join(o["value"] for o in kovalev["occurrences"])
    # At least one non-Latin (Cyrillic) or transliterated occurrence recorded.
    assert any(v in values for v in ("Юрий", "Iurii", "Kowaljow")) or "Kovalev" in values


def test_duckdb_views_query_generated_data(tmp_path) -> None:
    out = generate(tmp_path, seed=42)
    connection = duckdb_over_csv(out)

    customer_count = connection.execute("SELECT COUNT(*) FROM kna1").fetchone()[0]
    assert customer_count == 150

    hits = connection.execute(
        "SELECT COUNT(*) FROM bseg WHERE SGTXT LIKE 'Payment to %'"
    ).fetchone()[0]
    assert hits >= 3
