"""PII service: scan a dataset directory, pseudonymize it, keep evidence.

This is the orchestration layer the API routes (and later the agent's
data-preparation step) call. It works over a directory of CSVs — the
synthetic dataset now, exported Azure SQL tables at the event.

Row-key convention matches the ground truth: first column of the table,
except BSEG where the key is "BELNR/BUZEI" (accounting line items).
"""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import get_settings
from app.pii.detector import detect
from app.pii.fuzzy import score_cell, score_text
from app.pii.pseudonymize import Pseudonymizer

# Columns treated as "the whole cell is a name" vs "name may hide in text".
NAME_COLUMNS = {"NAME1", "USNAM"}
TEXT_COLUMNS = {"SGTXT"}
DEFAULT_THRESHOLD = 80.0


@dataclass
class Finding:
    table: str
    row_key: str
    column: str
    value: str
    matched_person: str
    score: float
    pii_type: str
    method: str


def _row_key(table: str, row: dict) -> str:
    if table == "bseg":
        return f"{row.get('BELNR', '')}/{row.get('BUZEI', '')}"
    first_column = next(iter(row))
    return str(row[first_column])


def _iter_tables(directory: Path):
    for csv_path in sorted(directory.glob("*.csv")):
        with csv_path.open(newline="") as handle:
            yield csv_path.stem, list(csv.DictReader(handle))


def scan(
    directory: str | Path,
    targets: list[str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[Finding]:
    """Find every occurrence of the target persons across all tables."""
    findings: list[Finding] = []
    for table, rows in _iter_tables(Path(directory)):
        for row in rows:
            key = _row_key(table, row)
            for column, cell in row.items():
                if not cell:
                    continue
                if column in NAME_COLUMNS:
                    for target in targets:
                        match = score_cell(cell, target)
                        if match and match.score >= threshold:
                            findings.append(
                                Finding(
                                    table=table, row_key=key, column=column, value=cell,
                                    matched_person=match.matched_name, score=match.score,
                                    pii_type="PERSON_NAME", method=match.method,
                                )
                            )
                elif column in TEXT_COLUMNS:
                    for target in targets:
                        match = score_text(cell, target)
                        if match and match.score >= threshold:
                            findings.append(
                                Finding(
                                    table=table, row_key=key, column=column, value=cell,
                                    matched_person=match.matched_name, score=match.score,
                                    pii_type="PERSON_NAME", method=match.method,
                                )
                            )
                # Structured PII (emails, phones, IBANs) — regex engine only here:
                # fast and deterministic. Presidio NER joins at the event.
                for entity in detect(cell, use_presidio=False):
                    findings.append(
                        Finding(
                            table=table, row_key=key, column=column, value=entity.value,
                            matched_person="", score=entity.score * 100,
                            pii_type=entity.pii_type, method=entity.engine,
                        )
                    )
    return findings


def pseudonymize_dataset(
    directory: str | Path,
    out_dir: str | Path,
    targets: list[str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    """Write a pseudonymized copy of the dataset + the mapping vault.

    Keys (KUNNR, LIFNR, BELNR) are never touched — joins stay intact.
    """
    source = Path(directory)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    findings = scan(source, targets, threshold=threshold)
    by_location = {(f.table, f.row_key, f.column): f for f in findings
                   if f.pii_type == "PERSON_NAME"}

    pseudonymizer = Pseudonymizer(secret_key=get_settings().pii_secret_key)
    replaced = 0

    for table, rows in _iter_tables(source):
        for row in rows:
            key = _row_key(table, row)
            for column in list(row.keys()):
                finding = by_location.get((table, key, column))
                if finding is None:
                    continue
                cell = row[column]
                if column in TEXT_COLUMNS:
                    # Replace only the name inside the sentence, keep the rest.
                    row[column] = _replace_in_text(cell, finding.matched_person, pseudonymizer)
                else:
                    row[column] = pseudonymizer.replace_name(cell, finding.matched_person)
                replaced += 1
            # Derived PII for pseudonymized persons: swap the email too.
            if "SMTP_ADDR" in row and (table, key, "NAME1") in by_location:
                person = by_location[(table, key, "NAME1")].matched_person
                row["SMTP_ADDR"] = pseudonymizer.identity_for(person)["email"]

        out_path = target_dir / f"{table}.csv"
        with out_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    vault_path = pseudonymizer.export_vault(target_dir / "pseudonym_vault.json")
    return {
        "findings": [asdict(f) for f in findings],
        "replaced_cells": replaced,
        "vault": str(vault_path),
        "output_dir": str(target_dir),
    }


def _replace_in_text(text: str, canonical: str, pseudonymizer: Pseudonymizer) -> str:
    """Swap the best-matching token window for the fake name, keep the sentence."""
    tokens = text.split()
    target_width = len(canonical.split())
    best_span: tuple[int, int] | None = None
    best_score = 0.0
    for width in (target_width, target_width + 1):
        for start in range(len(tokens) - width + 1):
            window = " ".join(tokens[start : start + width])
            match = score_text(window, canonical)
            if match and match.score > best_score:
                best_score = match.score
                best_span = (start, start + width)
    if best_span is None or best_score < DEFAULT_THRESHOLD:
        return text
    replacement = pseudonymizer.replace_name(
        " ".join(tokens[best_span[0] : best_span[1]]), canonical
    )
    return " ".join(tokens[: best_span[0]] + [replacement] + tokens[best_span[1] :])
