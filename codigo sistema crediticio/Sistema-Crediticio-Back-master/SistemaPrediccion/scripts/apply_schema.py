"""Apply the credit-engine schema to a target database (Azure SQL compatible).

Runs the table/index batches of ``create_database.sql`` against the database
the URL points at. The ``CREATE DATABASE`` / ``USE`` preamble is skipped:
Azure SQL Database does not support ``USE`` (you connect straight to the
target database), and database provisioning there belongs to the portal.

    python scripts/apply_schema.py --url "mssql+pymssql://user:pass@server:1433/CreditEngine"
    python scripts/apply_schema.py                # CREDIT_ENGINE_DATABASE_URL / SQLite

Idempotent — the DDL's IF-NOT-EXISTS guards make re-runs safe.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from credit_engine.database import build_engine
except ImportError:  # running as a plain script without the package installed
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from credit_engine.database import build_engine

_SQL_FILE = Path(__file__).resolve().parent / "create_database.sql"


def _batches(sql_text: str) -> list[str]:
    """Split on GO lines and drop batches Azure SQL can't run in-database."""
    raw_batches = re.split(r"(?im)^\s*GO\s*$", sql_text)
    runnable: list[str] = []
    for batch in raw_batches:
        stripped = batch.strip()
        if not stripped:
            continue
        no_comments = re.sub(r"/\*.*?\*/", "", stripped, flags=re.S)
        if re.search(r"(?i)\bCREATE\s+DATABASE\b", no_comments) or re.match(r"(?i)\s*USE\b", no_comments):
            continue
        runnable.append(stripped)
    return runnable


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the credit-engine schema to the target database")
    parser.add_argument(
        "--url",
        default=None,
        help="Database URL pointing AT the target database (default: CREDIT_ENGINE_DATABASE_URL)",
    )
    args = parser.parse_args()

    engine = build_engine(args.url)
    if engine.dialect.name != "mssql":
        print(f"Dialect is '{engine.dialect.name}' — use create_all()/seed scripts for non-SQL-Server targets")
        sys.exit(1)

    batches = _batches(_SQL_FILE.read_text(encoding="utf-8"))
    with engine.connect() as connection:
        for i, batch in enumerate(batches, start=1):
            connection.exec_driver_sql(batch)
            connection.commit()
    print(f"Applied {len(batches)} schema batches to {engine.url.host}/{engine.url.database}")


if __name__ == "__main__":
    main()
