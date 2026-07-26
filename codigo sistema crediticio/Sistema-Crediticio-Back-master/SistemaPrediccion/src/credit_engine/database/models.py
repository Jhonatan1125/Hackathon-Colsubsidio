"""SQLAlchemy ORM models mirroring ``scripts/create_database.sql``.

The T-SQL script is the **source of truth for production** (SQL Server);
these models are the portable in-code mirror — identical table and column
names, engine-agnostic types — so the same ORM runs against SQL Server
(``mssql+pyodbc``) in production and SQLite in tests/local development
(``Base.metadata.create_all``).

Conventions shared with the DDL:

- Multi-label dataset columns (``intereses``, ``momentos_clave``, …) are
  stored as JSON array strings (e.g. ``'["educacion","turismo"]'``);
  ``repositories.py`` converts them to and from Python lists.
- ``trigger`` is reserved in T-SQL, so the column is ``trigger_event``
  (mapped back to ``ScheduledMessage.trigger`` by the repository).
- Batch IDs are opaque app-generated strings (lowercase ``uuid4`` from the
  ingestion queue) stored as ``NVARCHAR(36)`` — never ``UNIQUEIDENTIFIER``,
  which pyodbc reads back UPPERCASED and would break Python-side equality.
- Timestamps are stored **naive UTC** (matching ``SYSUTCDATETIME()``);
  the repositories re-attach UTC when returning contract objects.
- ``Unicode``/``UnicodeText`` render as NVARCHAR on SQL Server so Spanish
  text survives even if ``create_all`` is ever pointed at a mssql URL.
- Column DEFAULTs here are **Python-side only** (applied on ORM inserts);
  the DDL owns the server-side DEFAULT constraints.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Unicode,
    UnicodeText,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> dt.datetime:
    """Naive UTC now — matches the DDL's SYSUTCDATETIME() semantics."""
    return dt.datetime.now(dt.UTC).replace(tzinfo=None)


def _new_batch_id() -> str:
    """Lowercase UUID4 string — same format the ingestion queue issues."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Declarative base for all credit-engine tables."""


class Person(Base):
    """Person profile — dataset schema per ``encoding/column_definitions.py``
    plus the delivery contact/consent fields (ROOT §7.1)."""

    __tablename__ = "persons"

    cedula: Mapped[str] = mapped_column(Unicode(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    correo: Mapped[str | None] = mapped_column(Unicode(320))
    direccion: Mapped[str | None] = mapped_column(Unicode(300))
    fecha_nacimiento: Mapped[dt.date | None] = mapped_column(Date)
    telefono: Mapped[str | None] = mapped_column(Unicode(30))

    consent_whatsapp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    edad: Mapped[int] = mapped_column(Integer, nullable=False)
    ingresos: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    score_datacredito: Mapped[int | None] = mapped_column(Integer)
    num_creditos_activos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deuda_total_acumulada_cop: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    cuota_mensual_total_cop: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    capacidad_endeudamiento_disponible_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0
    )

    categoria_afiliacion: Mapped[str] = mapped_column(Unicode(1), nullable=False)
    mora_maxima_historica: Mapped[str] = mapped_column(Unicode(12), nullable=False, default="0_DIAS")

    area_trabajo: Mapped[str | None] = mapped_column(Unicode(500))
    intereses: Mapped[str | None] = mapped_column(Unicode(500))
    preferencias: Mapped[str | None] = mapped_column(Unicode(500))
    momentos_clave: Mapped[str | None] = mapped_column(Unicode(500))
    composicion_familiar: Mapped[str | None] = mapped_column(Unicode(500))
    historial_creditos: Mapped[str | None] = mapped_column(Unicode(500))

    producto_colsubsidio_target: Mapped[str | None] = mapped_column(Unicode(60))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )


class Batch(Base):
    """Batch tracking — mirrors the ingestion ``BatchResult`` lifecycle."""

    __tablename__ = "batches"

    batch_id: Mapped[str] = mapped_column(Unicode(36), primary_key=True, default=_new_batch_id)
    status: Mapped[str] = mapped_column(Unicode(12), nullable=False, default="queued")
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report: Mapped[str | None] = mapped_column(UnicodeText)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime)


class BatchPerson(Base):
    """Per-person outcome inside a batch — mirrors the worker ``PersonResult``.

    No FK to persons: a submitted ID may legitimately not exist
    (``person_not_found`` is a valid outcome to record).
    """

    __tablename__ = "batch_persons"

    batch_id: Mapped[str] = mapped_column(
        Unicode(36), ForeignKey("batches.batch_id", ondelete="CASCADE"), primary_key=True
    )
    cedula: Mapped[str] = mapped_column(Unicode(20), primary_key=True)
    result_status: Mapped[str | None] = mapped_column(Unicode(20))
    detail: Mapped[str | None] = mapped_column(Unicode(1000))


class ScheduledMessageRecord(Base):
    """Outbox row — mirrors the worker ``ScheduledMessage`` contract.

    ``batch_id`` is a plain indexed column (no FK): batches currently
    live in the in-memory ingestion queue, so a batches row may not
    exist yet when a message is stored. The FK gets restored when batch
    persistence (a DB-backed ``BatchQueue``) lands.
    """

    __tablename__ = "scheduled_messages"

    message_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    batch_id: Mapped[str | None] = mapped_column(Unicode(36), index=True)
    cedula: Mapped[str] = mapped_column(Unicode(20), ForeignKey("persons.cedula"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(Unicode(50), nullable=False)

    amount_cop: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    annual_rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 3))
    term_months: Mapped[int | None] = mapped_column(Integer)
    cuota_cop: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    channel: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    contact_window: Mapped[str] = mapped_column(Unicode(12), nullable=False)
    trigger_event: Mapped[str] = mapped_column(Unicode(100), nullable=False, default="inmediato")
    message_text: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    message_source: Mapped[str] = mapped_column(Unicode(10), nullable=False, default="template")
    status: Mapped[str] = mapped_column(Unicode(10), nullable=False, default="scheduled")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=_utcnow)
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
