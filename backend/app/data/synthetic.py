"""Synthetic SAP-like dataset with PII ground truth.

Why this exists: Stages 3-6 need data where we KNOW exactly which cell
contains whose personal data. Real dumps never come with that answer key;
this generator produces one. The eval panel (Stage 6) measures precision
and recall against the ground_truth.json produced here.

Design choices:
- Table and column names follow real SAP ERP conventions (KNA1 customers,
  LFA1 vendors, BKPF/BSEG accounting documents, NAME1, SGTXT, USNAM).
  When the agent answers "found in KNA1.NAME1", the DMI jury reads that
  as domain knowledge.
- Tracked persons include the 2025 official test cases ("Paul Jonas",
  "Paula Erickson") and a Cyrillic/transliteration case (Yuri Kovalev)
  for the multilingual bonus.
- Names appear in fuzzy variants ("Jonas, Paul", "P. Jonas", typos) and
  inside free text (SGTXT), exactly like a 20-year-old ERP.
- Fully deterministic: same seed -> byte-identical output.

CLI:
    python -m app.data.synthetic --out data/synthetic --seed 42
"""

import argparse
import csv
import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from faker import Faker

# ── Tracked persons ──────────────────────────────────────────────────
# These are the people the ground truth records. Everything else in the
# dataset is realistic noise (untracked Faker names).

TRACKED_CANONICAL: list[dict] = [
    # 2025 hackathon official test cases: each must yield >= 3 matches.
    {"person_id": "person_001", "name": "Paul Jonas"},
    {"person_id": "person_002", "name": "Paula Erickson"},
    # Multilingual case: Cyrillic + transliteration variants.
    {
        "person_id": "person_003",
        "name": "Yuri Kovalev",
        "extra_variants": ["Юрий Ковалёв", "Iurii Kovalov", "Kowaljow, Juri"],
    },
]


def _name_variants(name: str, rng: random.Random) -> list[str]:
    """Fuzzy spellings of one name, as found in legacy ERP data."""
    first, last = name.split(" ", 1)
    variants = [
        name,                          # Paul Jonas
        f"{last}, {first}",            # Jonas, Paul
        f"{first[0]}. {last}",         # P. Jonas
        name.upper(),                  # PAUL JONAS
    ]
    # One typo variant: swap two adjacent letters in the last name.
    if len(last) >= 4:
        i = rng.randrange(1, len(last) - 2)
        typo = last[:i] + last[i + 1] + last[i] + last[i + 2:]
        variants.append(f"{first} {typo}")  # Paul Jnoas
    return variants


@dataclass
class GroundTruth:
    """Answer key: every occurrence of every tracked person."""

    seed: int
    entities: list[dict] = field(default_factory=list)

    def add(
        self,
        person_id: str,
        canonical: str,
        *,
        table: str,
        row_key: str,
        column: str,
        value: str,
        pii_type: str = "PERSON_NAME",
    ) -> None:
        entity = next(
            (e for e in self.entities if e["person_id"] == person_id), None
        )
        if entity is None:
            entity = {
                "person_id": person_id,
                "canonical_name": canonical,
                "occurrences": [],
            }
            self.entities.append(entity)
        entity["occurrences"].append(
            {
                "table": table,
                "row_key": row_key,
                "column": column,
                "value": value,
                "pii_type": pii_type,
            }
        )


def generate(
    out_dir: str | Path,
    *,
    seed: int = 42,
    customers: int = 150,
    vendors: int = 80,
    documents: int = 400,
) -> Path:
    """Write kna1/lfa1/bkpf/bseg CSVs + ground_truth.json into `out_dir`."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    fake = Faker("de_CH")  # Swiss-German locale: fits the JiVS context
    Faker.seed(seed)

    truth = GroundTruth(seed=seed)

    # Assign each tracked person their fuzzy variants up front.
    tracked: list[dict] = []
    for spec in TRACKED_CANONICAL:
        variants = _name_variants(spec["name"], rng) + spec.get("extra_variants", [])
        tracked.append({**spec, "variants": variants})

    # ── KNA1: customer master ────────────────────────────────────────
    kna1_rows: list[dict] = []
    for index in range(customers):
        kunnr = f"{1000 + index:010d}"
        if index < len(tracked):  # tracked persons occupy the first rows
            person = tracked[index]
            name = person["variants"][0]
            first, last = person["name"].lower().split(" ", 1)
            email = f"{first}.{last}@example.com"
            kna1_rows.append(_customer_row(kunnr, name, email, fake))
            truth.add(person["person_id"], person["name"],
                      table="kna1", row_key=kunnr, column="NAME1", value=name)
            truth.add(person["person_id"], person["name"],
                      table="kna1", row_key=kunnr, column="SMTP_ADDR",
                      value=email, pii_type="EMAIL")
        else:
            kna1_rows.append(_customer_row(kunnr, fake.name(), fake.email(), fake))

    # ── LFA1: vendor master (tracked persons appear again, variant form) ─
    lfa1_rows: list[dict] = []
    for index in range(vendors):
        lifnr = f"{7000 + index:010d}"
        if index < len(tracked):
            person = tracked[index]
            variant = person["variants"][1]  # "Last, First" form
            lfa1_rows.append(_vendor_row(lifnr, variant, fake))
            truth.add(person["person_id"], person["name"],
                      table="lfa1", row_key=lifnr, column="NAME1", value=variant)
        else:
            lfa1_rows.append(_vendor_row(lifnr, fake.company(), fake))

    # ── BKPF + BSEG: accounting documents with free-text PII ─────────
    bkpf_rows: list[dict] = []
    bseg_rows: list[dict] = []
    for index in range(documents):
        belnr = f"{5000000 + index:010d}"
        bkpf_rows.append(
            {
                "BELNR": belnr,
                "BUKRS": "CH01",
                "GJAHR": rng.choice(["2018", "2019", "2020", "2021"]),
                "BUDAT": fake.date_between("-8y", "-1y").isoformat(),
                "USNAM": fake.user_name().upper()[:12],
            }
        )
        amount = round(rng.uniform(50, 250_000), 2)
        # Every ~40th document mentions a tracked person inside free text —
        # the hardest PII location: unstructured, variant spelling.
        if index % 40 == 0 and tracked:
            person = tracked[(index // 40) % len(tracked)]
            variant = rng.choice(person["variants"])
            sgtxt = f"Payment to {variant} re invoice {rng.randrange(10_000, 99_999)}"
            truth.add(person["person_id"], person["name"],
                      table="bseg", row_key=f"{belnr}/001", column="SGTXT", value=sgtxt)
        else:
            sgtxt = rng.choice(
                ["Monthly service fee", "Hardware purchase", "Consulting Q3",
                 "Freight costs", "License renewal"]
            )
        bseg_rows.append(
            {
                "BELNR": belnr,
                "BUZEI": "001",
                "KUNNR": rng.choice(kna1_rows)["KUNNR"],
                "WRBTR": f"{amount:.2f}",
                "WAERS": "CHF",
                "SGTXT": sgtxt,
            }
        )

    _write_csv(out / "kna1.csv", kna1_rows)
    _write_csv(out / "lfa1.csv", lfa1_rows)
    _write_csv(out / "bkpf.csv", bkpf_rows)
    _write_csv(out / "bseg.csv", bseg_rows)

    truth_payload = {"seed": seed, "entities": truth.entities}
    (out / "ground_truth.json").write_text(
        json.dumps(truth_payload, indent=2, ensure_ascii=False, sort_keys=True)
    )
    return out


def _customer_row(kunnr: str, name: str, email: str, fake: Faker) -> dict:
    return {
        "KUNNR": kunnr,
        "NAME1": name,
        "ORT01": fake.city(),
        "STRAS": fake.street_address(),
        "TELF1": fake.phone_number(),
        "SMTP_ADDR": email,
    }


def _vendor_row(lifnr: str, name: str, fake: Faker) -> dict:
    return {
        "LIFNR": lifnr,
        "NAME1": name,
        "ORT01": fake.city(),
        "STRAS": fake.street_address(),
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic SAP-like dataset")
    parser.add_argument("--out", default="data/synthetic")
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    target = generate(arguments.out, seed=arguments.seed)
    print(f"Dataset written to {target.resolve()}")


if __name__ == "__main__":
    main()
