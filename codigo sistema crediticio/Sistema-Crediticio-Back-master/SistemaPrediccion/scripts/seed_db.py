"""Seed the credit-engine database with the demo personas.

Loads the 12 demo personas (``worker/demo.py`` — dataset schema) into the
``persons`` table so the API + worker flow runs against a real database:

    python scripts/seed_db.py                          # SQLite default (credit_engine.db)
    python scripts/seed_db.py --url "mssql+pyodbc://..."   # SQL Server

For SQLite/local the tables are created automatically; for SQL Server run
``scripts/create_database.sql`` first (it owns the CHECK constraints and
indexes), then point --url (or CREDIT_ENGINE_DATABASE_URL) at it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from credit_engine.database import build_engine, create_all, create_session_factory
except ImportError:  # running as a plain script without the package installed
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from credit_engine.database import build_engine, create_all, create_session_factory

from credit_engine.database.repositories import SqlPersonRepository
from credit_engine.worker.demo import DEMO_PERSONS


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the database with demo personas")
    parser.add_argument(
        "--url",
        default=None,
        help="Database URL (default: CREDIT_ENGINE_DATABASE_URL env var, then local SQLite)",
    )
    args = parser.parse_args()

    engine = build_engine(args.url)
    create_all(engine)
    repository = SqlPersonRepository(create_session_factory(engine))

    for person in DEMO_PERSONS.values():
        repository.save_person(person)

    print(f"Seeded {len(DEMO_PERSONS)} personas into {engine.url}")


if __name__ == "__main__":
    main()
