"""The agent: natural-language question -> cited answer over enterprise data.

Pipeline (one ask() call):
1. RETRIEVE   top-k schema cards for the question (catalog.retrieve)
2. GENERATE   SQL via structured output on the SMART tier; the system
              prompt with schema cards is marked for prompt caching
3. POLICY     parse + sanitize the SQL (policy.check) — hard barrier
4. EXECUTE    against DuckDB (synthetic dataset now, exports at the event)
5. ANSWER     synthesize a short answer from the result set, with
              citations (table, key rows) attached mechanically —
              not generated, so they cannot be hallucinated

Every step's artifacts (sql, violations, citations, cost) are returned:
the frontend shows them, the eval panel measures them.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from app.agent.catalog import TableCard, build_catalog, retrieve
from app.agent.policy import check
from app.data.connectors import duckdb_over_csv
from app.guardrails.input_filter import inspect_input
from app.guardrails.output_filter import inspect_output
from app.llm.client import LLMClient, Tier
from app.llm.cost import get_meter

MAX_RESULT_ROWS_IN_PROMPT = 30

SYSTEM_TEMPLATE = """You are a careful data analyst for an enterprise archive.
You answer questions ONLY from the tables described below.
Rules:
- Use only listed tables and columns. Never invent names.
- Prefer aggregate answers with the rows that support them.
- Dialect: DuckDB SQL.

{schema_cards}"""


class GeneratedSQL(BaseModel):
    sql: str = Field(description="One DuckDB SELECT statement")
    tables_used: list[str]
    rationale: str = Field(description="One sentence: why this query answers it")


class Citation(BaseModel):
    table: str
    rows: list[dict]


class AgentAnswer(BaseModel):
    answer: str
    sql: str
    citations: list[Citation]
    row_count: int
    rejected: bool = False
    violations: list[str] = []
    blocked_input: bool = False
    output_redacted: bool = False
    cost_usd: float = 0.0


class DataAgent:
    def __init__(
        self,
        data_dir: str | Path,
        llm: LLMClient | None = None,
        *,
        guard_with_llm: bool = False,
    ) -> None:
        self._connection = duckdb_over_csv(data_dir)
        self._catalog = build_catalog(self._connection)
        self._llm = llm or LLMClient()
        self._guard_with_llm = guard_with_llm

    def ask(self, question: str) -> AgentAnswer:
        cost_before = get_meter().snapshot()["cost_usd"]

        # 0. Input guardrail (layer 1): block prompt injection before anything runs.
        guard = inspect_input(
            question, llm=self._llm if self._guard_with_llm else None
        )
        if guard.blocked:
            return AgentAnswer(
                answer="This request was blocked by the security filter.",
                sql="", citations=[], row_count=0,
                rejected=True, blocked_input=True,
                violations=[f"{guard.layer}: {guard.reason}"],
                cost_usd=round(get_meter().snapshot()["cost_usd"] - cost_before, 6),
            )

        # 1. Retrieve relevant schema cards.
        cards = retrieve(question, self._catalog)
        system = SYSTEM_TEMPLATE.format(
            schema_cards="\n\n".join(card.render() for card in cards)
        )

        # 2. Generate SQL (structured, validated, auto-retry inside).
        generated = self._llm.structured(
            f"Question: {question}\nWrite the SQL.",
            GeneratedSQL,
            tier=Tier.SMART,
            system=system,
        )

        # 3. Policy barrier. The allowlist is the FULL catalog, not just the
        # retrieved cards: retrieval decides what schema to show the model,
        # but every real table is legitimately queryable. Checking against the
        # retrieved subset alone would reject valid SQL whenever ranking is
        # imperfect (e.g. a short table name diluted by fuzzy scoring).
        result = check(
            generated.sql, allowed_tables=[card.name for card in self._catalog]
        )
        if not result.allowed:
            return AgentAnswer(
                answer="The requested query is not permitted under the data access policy.",
                sql=generated.sql,
                citations=[],
                row_count=0,
                rejected=True,
                violations=result.violations,
                cost_usd=round(get_meter().snapshot()["cost_usd"] - cost_before, 6),
            )

        # 4. Execute sanitized SQL.
        cursor = self._connection.execute(result.sql)
        column_names = [description[0] for description in cursor.description]
        rows = [dict(zip(column_names, row, strict=True)) for row in cursor.fetchall()]

        # 5. Synthesize the answer; citations are attached mechanically.
        preview = rows[:MAX_RESULT_ROWS_IN_PROMPT]
        synthesis = self._llm.complete(
            f"Question: {question}\n"
            f"SQL executed: {result.sql}\n"
            f"Result rows ({len(rows)} total, first {len(preview)} shown): {preview}\n"
            "Answer the question in 1-3 sentences, stating concrete numbers.",
            tier=Tier.SMART,
            system="You summarize query results precisely. Never invent values.",
        )

        # 6. Output guardrail (layer 4): redact restricted PII from the answer.
        output_scan = inspect_output(synthesis.text.strip())

        citations = _citations_from_rows(generated.tables_used, cards, preview)
        return AgentAnswer(
            answer=output_scan.redacted_text,
            sql=result.sql,
            citations=citations,
            row_count=len(rows),
            output_redacted=not output_scan.safe,
            cost_usd=round(get_meter().snapshot()["cost_usd"] - cost_before, 6),
        )


def _citations_from_rows(
    tables_used: list[str], cards: list[TableCard], rows: list[dict]
) -> list[Citation]:
    """Attach the evidence rows to the tables the query used."""
    known = {card.name for card in cards}
    cited_tables = [table for table in tables_used if table in known] or sorted(known)
    return [Citation(table=table, rows=rows[:10]) for table in cited_tables[:3]]
