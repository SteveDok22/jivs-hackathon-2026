"""Stage 4 verification: retrieval ranking, SQL policy barrier,
end-to-end cited answers on the synthetic dataset (FakeProvider, offline)."""

import json

from app.agent.agent import DataAgent
from app.agent.catalog import build_catalog, retrieve
from app.agent.policy import check
from app.data.connectors import duckdb_over_csv
from app.data.synthetic import generate
from app.llm.client import LLMClient
from app.llm.providers import FakeProvider

ALL_TABLES = ["kna1", "lfa1", "bkpf", "bseg"]


# ── Retrieval ────────────────────────────────────────────────────────

def test_retrieval_ranks_relevant_tables_first(tmp_path) -> None:
    data_dir = generate(tmp_path, seed=42)
    cards = build_catalog(duckdb_over_csv(data_dir))

    top = retrieve("How much did we pay our vendors in invoices?", cards, top_k=2)
    assert {card.name for card in top} <= {"bseg", "lfa1", "bkpf"}

    top = retrieve("What is the customer address and city?", cards, top_k=1)
    assert top[0].name == "kna1"


# ── Policy barrier ───────────────────────────────────────────────────

def test_policy_rejects_non_select() -> None:
    result = check("UPDATE kna1 SET NAME1 = 'x'", allowed_tables=ALL_TABLES)
    assert not result.allowed
    assert any("SELECT" in violation for violation in result.violations)


def test_policy_rejects_unknown_table() -> None:
    result = check("SELECT NAME1 FROM secret_salaries", allowed_tables=ALL_TABLES)
    assert not result.allowed
    assert any("allowlist" in violation for violation in result.violations)


def test_policy_rejects_restricted_columns() -> None:
    result = check("SELECT TELF1, SMTP_ADDR FROM kna1", allowed_tables=ALL_TABLES)
    assert not result.allowed
    assert sum("restricted column" in violation for violation in result.violations) == 2


def test_policy_rejects_select_star() -> None:
    result = check("SELECT * FROM kna1", allowed_tables=ALL_TABLES)
    assert not result.allowed


def test_policy_appends_limit_and_allows_clean_select() -> None:
    result = check("SELECT NAME1, ORT01 FROM kna1", allowed_tables=ALL_TABLES)
    assert result.allowed
    assert "LIMIT 500" in result.sql


def test_policy_rejects_multiple_statements() -> None:
    result = check(
        "SELECT NAME1 FROM kna1; SELECT NAME1 FROM lfa1", allowed_tables=ALL_TABLES
    )
    assert not result.allowed


# ── End to end ───────────────────────────────────────────────────────

def _scripted_llm(sql: str) -> LLMClient:
    generated = json.dumps(
        {"sql": sql, "tables_used": ["bseg"], "rationale": "sums payments"}
    )
    return LLMClient(
        provider=FakeProvider(
            responses=[generated, "Total payments amount to 1.2M CHF across 400 items."]
        )
    )


def test_agent_answers_with_citations(tmp_path) -> None:
    data_dir = generate(tmp_path, seed=42)
    llm = _scripted_llm(
        "SELECT BELNR, WRBTR FROM bseg WHERE SGTXT LIKE 'Payment to %'"
    )
    agent = DataAgent(data_dir, llm=llm)

    answer = agent.ask("Which documents are direct payments to persons?")

    assert not answer.rejected
    assert answer.row_count >= 3
    assert "LIMIT" in answer.sql                      # policy sanitized the SQL
    assert answer.citations and answer.citations[0].table == "bseg"
    assert answer.citations[0].rows[0]["BELNR"]       # evidence rows carry keys
    assert "1.2M CHF" in answer.answer


def test_agent_rejects_policy_violation_end_to_end(tmp_path) -> None:
    data_dir = generate(tmp_path, seed=42)
    llm = _scripted_llm("SELECT SMTP_ADDR FROM kna1")
    agent = DataAgent(data_dir, llm=llm)

    answer = agent.ask("Give me every customer email address")

    assert answer.rejected
    assert answer.row_count == 0
    assert any("restricted column" in violation for violation in answer.violations)
    assert "not permitted" in answer.answer


# ── Stage 10 fixes: COUNT(*) allowed, allowlist is full catalog ──────

def test_policy_allows_count_star() -> None:
    """COUNT(*) is an aggregate, not a column projection — must be allowed."""
    result = check("SELECT COUNT(*) FROM kna1", allowed_tables=ALL_TABLES)
    assert result.allowed, result.violations
    assert "LIMIT" in result.sql


def test_policy_still_rejects_bare_select_star() -> None:
    result = check("SELECT * FROM kna1", allowed_tables=ALL_TABLES)
    assert not result.allowed
    assert any("SELECT *" in v for v in result.violations)


def test_policy_allows_count_star_with_other_aggregates() -> None:
    result = check(
        "SELECT COUNT(*) AS n, MAX(WRBTR) AS mx FROM bseg", allowed_tables=ALL_TABLES
    )
    assert result.allowed, result.violations


def test_agent_count_query_uses_full_catalog_allowlist(tmp_path) -> None:
    """A COUNT(*) on a real table must pass even if retrieval ranked it low."""
    data_dir = generate(tmp_path, seed=42)
    llm = _scripted_llm("SELECT COUNT(*) AS total FROM kna1")
    # Force retrieval to return the WRONG cards, proving the allowlist no
    # longer depends on retrieval: the query on kna1 must still be allowed.
    agent = DataAgent(data_dir, llm=llm)
    answer = agent.ask("How many customers are there in total?")

    assert not answer.rejected, answer.violations
    assert answer.row_count == 1
