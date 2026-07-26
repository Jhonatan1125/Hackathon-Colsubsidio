import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from credit_engine.database.connection import enable_sqlite_foreign_keys
from credit_engine.database.models import Base


@pytest.fixture
def session_factory():
    """In-memory SQLite engine shared across sessions (StaticPool keeps the
    single connection alive so every session sees the same database).
    FK enforcement is on, matching SQL Server semantics."""
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()
