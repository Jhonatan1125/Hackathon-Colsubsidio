"""Engine and session factory — connection management for the data layer.

The database URL comes from the ``CREDIT_ENGINE_DATABASE_URL`` environment
variable, defaulting to a local SQLite file so everything works with zero
infrastructure. For SQL Server (the provisioned production engine, see
``scripts/create_database.sql``) install the ``mssql`` extra
(``pip install .[mssql]``) and set::

    CREDIT_ENGINE_DATABASE_URL="mssql+pyodbc://user:pass@server/CreditEngine?driver=ODBC+Driver+18+for+SQL+Server"
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from credit_engine.database.models import Base

DATABASE_URL_ENV_VAR = "CREDIT_ENGINE_DATABASE_URL"
DEFAULT_DATABASE_URL = "sqlite:///credit_engine.db"


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """Turn on SQLite FK enforcement (OFF by default) for every connection.

    Keeps local/dev/test behavior aligned with SQL Server, where the FKs
    the DDL declares are always enforced — otherwise FK bugs stay
    invisible until production. No-op for non-SQLite engines.
    """
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _connection_record):  # noqa: ANN001 — DBAPI signature
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def build_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine.

    Args:
        url: Explicit database URL. Falls back to the
            ``CREDIT_ENGINE_DATABASE_URL`` environment variable, then to
            the local SQLite default.
        echo: Log emitted SQL (debugging).
    """
    resolved = url or os.environ.get(DATABASE_URL_ENV_VAR, DEFAULT_DATABASE_URL)
    engine = create_engine(resolved, echo=echo, pool_pre_ping=True)
    enable_sqlite_foreign_keys(engine)
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Session factory bound to the engine (one short-lived session per unit of work)."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_all(engine: Engine) -> None:
    """Create all tables from the ORM metadata.

    Convenience for SQLite/local development and tests. Production SQL
    Server provisioning uses ``scripts/create_database.sql`` (which adds
    the CHECK constraints and indexes the portable ORM omits).
    """
    Base.metadata.create_all(engine)
