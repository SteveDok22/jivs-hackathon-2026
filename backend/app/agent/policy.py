"""SQL policy: the barrier between the LLM and the database.

Generated SQL is never executed directly. It is parsed (sqlglot),
checked against an explicit policy, sanitized, and only then run.
On the pitch this is one sentence: "the model has no database access —
between them sit a parser and a policy". Architecture, not promises.

Checks:
1. Exactly one statement, and it is a SELECT (read-only by construction).
2. Every referenced table is on the allowlist (the catalog).
3. No denied columns (restricted PII: phones, emails — configurable).
4. SELECT * is rejected on tables that contain denied columns.
5. A LIMIT is enforced if missing (runaway result protection).
"""

from dataclasses import dataclass

import sqlglot
from sqlglot import exp

from app.config import get_settings


@dataclass
class PolicyResult:
    allowed: bool
    sql: str                 # sanitized SQL (only meaningful when allowed)
    violations: list[str]


def check(sql: str, *, allowed_tables: list[str]) -> PolicyResult:
    settings = get_settings()
    denied_columns = {column.lower() for column in settings.agent_denied_columns}
    allowed = {table.lower() for table in allowed_tables}
    violations: list[str] = []

    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as error:
        return PolicyResult(allowed=False, sql=sql, violations=[f"parse error: {error}"])

    if len(statements) != 1:
        return PolicyResult(
            allowed=False, sql=sql, violations=["exactly one statement required"]
        )
    statement = statements[0]

    if not isinstance(statement, exp.Select):
        violations.append(f"only SELECT is allowed, got {statement.key.upper()}")
        return PolicyResult(allowed=False, sql=sql, violations=violations)

    referenced_tables = {table.name.lower() for table in statement.find_all(exp.Table)}
    for table in sorted(referenced_tables - allowed):
        violations.append(f"table not on allowlist: {table}")

    for column in statement.find_all(exp.Column):
        if column.name.lower() in denied_columns:
            violations.append(f"restricted column: {column.name}")

    # Reject SELECT * (bare star in the projection) because it could leak
    # restricted columns. But COUNT(*) and other aggregates over * are safe —
    # the star there is a row marker, not a column projection. So we only
    # flag a Star whose parent is the SELECT itself, not a function call.
    for star in statement.find_all(exp.Star):
        parent = star.parent
        if isinstance(parent, exp.Column):
            parent = parent.parent
        if not isinstance(parent, (exp.Count, exp.Func)):
            violations.append(
                "SELECT * is not allowed; list the columns you need explicitly"
            )
            break

    if violations:
        return PolicyResult(allowed=False, sql=sql, violations=sorted(set(violations)))

    if statement.args.get("limit") is None:
        statement = statement.limit(settings.agent_max_rows)

    return PolicyResult(
        allowed=True, sql=statement.sql(dialect="duckdb"), violations=[]
    )
