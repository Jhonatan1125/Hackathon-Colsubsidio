"""Database layer — SQLAlchemy models, connection, and repositories.

Wire it into the worker (replacing the in-memory stand-ins)::

    from credit_engine.database import (
        SqlOutbox, SqlPersonRepository, build_engine, create_all, create_session_factory,
    )
    from credit_engine.worker import service

    engine = build_engine()            # CREDIT_ENGINE_DATABASE_URL or local SQLite
    create_all(engine)                 # SQLite/local; SQL Server uses scripts/create_database.sql
    factory = create_session_factory(engine)
    service.configure(
        repository=SqlPersonRepository(factory),
        outbox=SqlOutbox(factory),
    )
"""

from credit_engine.database.connection import (
    DATABASE_URL_ENV_VAR,
    DEFAULT_DATABASE_URL,
    build_engine,
    create_all,
    create_session_factory,
)
from credit_engine.database.models import (
    Base,
    Batch,
    BatchPerson,
    Person,
    ScheduledMessageRecord,
)
from credit_engine.database.repositories import SqlBatchRepository, SqlOutbox, SqlPersonRepository

__all__ = [
    "Base",
    "Person",
    "Batch",
    "BatchPerson",
    "ScheduledMessageRecord",
    "build_engine",
    "create_session_factory",
    "create_all",
    "DATABASE_URL_ENV_VAR",
    "DEFAULT_DATABASE_URL",
    "SqlPersonRepository",
    "SqlBatchRepository",
    "SqlOutbox",
]
