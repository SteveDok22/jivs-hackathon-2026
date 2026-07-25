"""Database connectors.

Three access paths, matching what the hackathon can throw at us:
- SQLAlchemy engine        -> our Postgres (docker) or Azure SQL (their 2025 setup)
- DuckDB over CSV/parquet  -> instant local analytics, no server needed
- The same engine factory is what the agent (Stage 4) will execute SQL through.

Azure SQL needs the optional `mssql` extra (pyodbc + ODBC Driver 18):
    pip install -e ".[dev,mssql]"
"""

from pathlib import Path

import duckdb
from sqlalchemy import Engine, create_engine

from app.config import get_settings


def get_engine(url: str | None = None) -> Engine:
    """Engine for the configured database (default: DATABASE_URL from .env)."""
    return create_engine(url or get_settings().database_url, pool_pre_ping=True)


def duckdb_over_csv(directory: str | Path) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with one view per CSV file in `directory`.

    View name = file stem, so data/synthetic/kna1.csv -> SELECT * FROM kna1.
    This is how Stages 3-6 query the synthetic dataset with zero setup.
    """
    connection = duckdb.connect()
    for csv_path in sorted(Path(directory).glob("*.csv")):
        view = csv_path.stem
        # CREATE VIEW cannot be a prepared statement in DuckDB, so the path
        # goes in as an escaped string literal instead of a bound parameter.
        path_literal = str(csv_path).replace("'", "''")
        connection.execute(
            f"CREATE VIEW {view} AS SELECT * FROM read_csv_auto('{path_literal}')"
        )
    return connection
