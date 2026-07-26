"""Schema catalog + retrieval: which tables are relevant to a question?

Why this exists: a real SAP ECC schema has thousands of tables and will
never fit into a prompt. The competitors' naive approach (dump the whole
schema) dies exactly there. We index every table as a "schema card"
(name, business description, columns, sample values) and retrieve only
the top-k relevant cards for each question.

Retrieval is deliberately TF-IDF-grade (keyword + fuzzy overlap, zero
extra dependencies, deterministic, offline). The upgrade path to vector
embeddings is one function swap — agreed in the stack document.
"""

from dataclasses import dataclass, field

import duckdb
from rapidfuzz import fuzz

# Domain knowledge: business meaning of SAP tables. When retrieval maps
# "payments to a vendor" onto BSEG/LFA1, that is this dictionary working.
SAP_DESCRIPTIONS: dict[str, str] = {
    "kna1": "customer master data: customer number name city street phone email address",
    "lfa1": "vendor supplier master data: vendor number name city street address",
    "bkpf": "accounting document header: document number company code fiscal year "
            "posting date entry user",
    "bseg": "accounting document line items: amounts currency payments invoices "
            "customer reference free text",
}


@dataclass
class TableCard:
    name: str
    description: str
    columns: list[tuple[str, str]]          # (column_name, type)
    sample_rows: list[dict] = field(default_factory=list)

    def render(self) -> str:
        """One card as prompt text."""
        column_list = ", ".join(f"{name} {dtype}" for name, dtype in self.columns)
        sample = "; ".join(
            ", ".join(f"{k}={v}" for k, v in row.items()) for row in self.sample_rows[:2]
        )
        return (
            f"TABLE {self.name}\n"
            f"  purpose: {self.description}\n"
            f"  columns: {column_list}\n"
            f"  sample: {sample}"
        )


def build_catalog(connection: duckdb.DuckDBPyConnection) -> list[TableCard]:
    """Introspect every view/table in the connection into schema cards."""
    cards: list[TableCard] = []
    tables = [row[0] for row in connection.execute("SHOW TABLES").fetchall()]
    for table in tables:
        columns = [
            (row[0], row[1])
            for row in connection.execute(f"DESCRIBE {table}").fetchall()
        ]
        cursor = connection.execute(f"SELECT * FROM {table} LIMIT 2")
        names = [description[0] for description in cursor.description]
        sample_rows = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
        description = SAP_DESCRIPTIONS.get(
            table, "table with columns: " + " ".join(name for name, _ in columns)
        )
        cards.append(
            TableCard(
                name=table, description=description,
                columns=columns, sample_rows=sample_rows,
            )
        )
    return cards


def retrieve(question: str, cards: list[TableCard], *, top_k: int = 3) -> list[TableCard]:
    """Rank schema cards by relevance to the question."""
    question_lower = question.lower()
    scored: list[tuple[float, TableCard]] = []
    for card in cards:
        document = f"{card.name} {card.description} " + " ".join(
            name.lower() for name, _ in card.columns
        )
        score = float(fuzz.token_set_ratio(question_lower, document))
        # Exact keyword hits outrank fuzzy overlap.
        for token in question_lower.split():
            if len(token) > 3 and token in document:
                score += 15
        scored.append((score, card))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [card for _, card in scored[:top_k]]
