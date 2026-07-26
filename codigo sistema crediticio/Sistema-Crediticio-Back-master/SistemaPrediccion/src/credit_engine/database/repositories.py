"""Repositories — all SQL lives here (repository pattern, root_project Piece 3).

Two repositories implement the worker's stage Protocols against the
database, replacing the in-memory stand-ins via
``worker.service.configure(repository=..., outbox=...)``:

- ``SqlPersonRepository`` → ``PersonRepository`` (DB Lookup stage)
- ``SqlOutbox``           → ``OutboxStore`` (Scheduled Message Store)

Both convert at the boundary so downstream consumers see the exact
person-dict / dataclass shapes the worker contracts define: multilabel
JSON strings become Python lists, ``Decimal`` becomes ``float``, and the
``trigger_event`` column maps back to ``ScheduledMessage.trigger``.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from credit_engine.database.models import Batch, BatchPerson, Person, ScheduledMessageRecord
from credit_engine.worker.contracts import PersonResult, ScheduledMessage

_MULTILABEL_FIELDS = (
    "area_trabajo",
    "intereses",
    "preferencias",
    "momentos_clave",
    "composicion_familiar",
    "historial_creditos",
)


def _dump_labels(values: list[str] | None) -> str | None:
    """Python list → JSON array string for storage (None stays None)."""
    return json.dumps(list(values), ensure_ascii=False) if values is not None else None


def _load_labels(raw: str | None) -> list[str]:
    """JSON array string → Python list (None/blank/malformed → empty list)."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [str(v) for v in parsed] if isinstance(parsed, list) else []


def _to_naive_utc(value: dt.datetime) -> dt.datetime:
    """Aware or naive datetime → naive UTC for storage (SYSUTCDATETIME semantics)."""
    if value.tzinfo is not None:
        return value.astimezone(dt.UTC).replace(tzinfo=None)
    return value


def _to_aware_utc(value: dt.datetime) -> dt.datetime:
    """Stored naive UTC → tz-aware UTC for contract objects.

    Keeps ``SqlOutbox`` behavior-compatible with ``InMemoryOutbox``:
    every ``ScheduledMessage`` the system hands out carries tz-aware UTC,
    so roundtrip equality holds and API serialization keeps its offset.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.UTC)
    return value


def _person_to_row_values(person: dict[str, Any]) -> dict[str, Any]:
    """Dataset-schema dict → Person column values (labels dumped, Decimals)."""
    values = dict(person)
    for field in _MULTILABEL_FIELDS:
        if field in values:
            values[field] = _dump_labels(values[field])
    for field in (
        "ingresos",
        "deuda_total_acumulada_cop",
        "cuota_mensual_total_cop",
        "capacidad_endeudamiento_disponible_pct",
    ):
        if values.get(field) is not None:
            values[field] = Decimal(str(values[field]))
    return values


def _person_to_dict(row: Person) -> dict[str, Any]:
    """ORM row → the person dict the worker/encoding contracts expect."""
    return {
        "cedula": row.cedula,
        "nombre": row.nombre,
        "correo": row.correo,
        "direccion": row.direccion,
        "fecha_nacimiento": row.fecha_nacimiento,
        "telefono": row.telefono,
        "consent_whatsapp": bool(row.consent_whatsapp),
        "consent_email": bool(row.consent_email),
        "edad": row.edad,
        "ingresos": float(row.ingresos),
        "score_datacredito": row.score_datacredito,
        "num_creditos_activos": row.num_creditos_activos,
        "deuda_total_acumulada_cop": float(row.deuda_total_acumulada_cop),
        "cuota_mensual_total_cop": float(row.cuota_mensual_total_cop),
        "capacidad_endeudamiento_disponible_pct": float(row.capacidad_endeudamiento_disponible_pct),
        "categoria_afiliacion": row.categoria_afiliacion,
        "mora_maxima_historica": row.mora_maxima_historica,
        **{field: _load_labels(getattr(row, field)) for field in _MULTILABEL_FIELDS},
        "producto_colsubsidio_target": row.producto_colsubsidio_target,
    }


class SqlPersonRepository:
    """``PersonRepository`` implementation over the ``persons`` table."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_person(self, person_id: str) -> dict[str, Any] | None:
        """Return the person dict for a sanitized ID, or None if unknown."""
        with self._session_factory() as session:
            row = session.get(Person, person_id)
            return _person_to_dict(row) if row is not None else None

    def get_persons_by_ids(self, person_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Bulk lookup: one SELECT for a whole batch (root_project Piece 3)."""
        if not person_ids:
            return {}
        with self._session_factory() as session:
            rows = session.scalars(select(Person).where(Person.cedula.in_(person_ids))).all()
            return {row.cedula: _person_to_dict(row) for row in rows}

    def save_person(self, person: dict[str, Any]) -> None:
        """Insert or update a person from a dataset-schema dict (seeding/tests)."""
        with self._session_factory() as session:
            session.merge(Person(**_person_to_row_values(person)))
            session.commit()

    def save_persons(self, persons: Iterable[dict[str, Any]], *, chunk_size: int = 1_000) -> int:
        """Bulk-insert persons (dataset loading — 20K rows in seconds).

        **Atomic**: one transaction, flushed per chunk to bound memory but
        committed once at the end — a failure (e.g. duplicate cédula
        IntegrityError) rolls everything back, never leaving a half-loaded
        table. Plain INSERTs, not upserts: use ``delete_all_persons`` first
        for a clean reload, or ``save_person`` for one-off upserts.
        Returns the inserted count.
        """
        total = 0
        with self._session_factory() as session:
            batch: list[Person] = []
            for person in persons:
                batch.append(Person(**_person_to_row_values(person)))
                if len(batch) >= chunk_size:
                    session.add_all(batch)
                    session.flush()
                    total += len(batch)
                    batch = []
            if batch:
                session.add_all(batch)
                session.flush()
                total += len(batch)
            session.commit()
        return total

    def delete_all_persons(self) -> int:
        """Remove every person row — dataset-replace semantics.

        Clears ``scheduled_messages`` first in the same transaction: the
        outbox FK references persons (no cascade), so deleting persons
        with stored messages would otherwise fail on SQL Server (and on
        SQLite with FK enforcement on). Returns the person rows removed.
        """
        with self._session_factory() as session:
            session.execute(delete(ScheduledMessageRecord))
            result = session.execute(delete(Person))
            session.commit()
            return result.rowcount or 0


class SqlOutbox:
    """``OutboxStore`` implementation over the ``scheduled_messages`` table."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, message: ScheduledMessage) -> None:
        """Persist one scheduled message."""
        with self._session_factory() as session:
            session.add(
                ScheduledMessageRecord(
                    batch_id=message.batch_id or None,
                    cedula=message.person_id,
                    product_id=message.product_id,
                    amount_cop=message.amount_cop,
                    annual_rate_pct=message.annual_rate_pct,
                    term_months=message.term_months,
                    cuota_cop=message.cuota_cop,
                    channel=message.channel,
                    contact_window=message.contact_window,
                    trigger_event=message.trigger,
                    message_text=message.message_text,
                    message_source=message.message_source,
                    status=message.status,
                    created_at=_to_naive_utc(message.created_at),
                )
            )
            session.commit()

    def for_person(self, person_id: str) -> list[ScheduledMessage]:
        """Every stored message for one person ID (insertion order)."""
        with self._session_factory() as session:
            rows = session.scalars(
                select(ScheduledMessageRecord)
                .where(ScheduledMessageRecord.cedula == person_id)
                .order_by(ScheduledMessageRecord.message_id)
            ).all()
            return [self._to_contract(row) for row in rows]

    def for_batch(self, batch_id: str) -> list[ScheduledMessage]:
        """Every stored message generated by one batch (insertion order)."""
        with self._session_factory() as session:
            rows = session.scalars(
                select(ScheduledMessageRecord)
                .where(ScheduledMessageRecord.batch_id == batch_id)
                .order_by(ScheduledMessageRecord.message_id)
            ).all()
            return [self._to_contract(row) for row in rows]

    @staticmethod
    def _to_contract(row: ScheduledMessageRecord) -> ScheduledMessage:
        return ScheduledMessage(
            person_id=row.cedula,
            product_id=row.product_id,
            channel=row.channel,
            contact_window=row.contact_window,
            trigger=row.trigger_event,
            message_text=row.message_text,
            message_source=row.message_source,
            batch_id=row.batch_id or "",
            status=row.status,
            created_at=_to_aware_utc(row.created_at),
            amount_cop=row.amount_cop,
            annual_rate_pct=row.annual_rate_pct,
            term_months=row.term_months,
            cuota_cop=row.cuota_cop,
        )


class SqlBatchRepository:
    """Persists batch lifecycle and per-person results to ``batches`` and ``batch_persons``.

    Called by the ``BatchProcessor`` alongside the in-memory queue so
    every batch transition and every person outcome lands in the database
    for audit, reporting, and cross-restart durability.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_batch(self, batch_id: str, total_count: int) -> None:
        """Upsert a batch row so the DB mirrors the in-memory queue entry."""
        with self._session_factory() as session:
            existing = session.get(Batch, batch_id)
            if existing is None:
                session.add(
                    Batch(
                        batch_id=batch_id,
                        status="queued",
                        total_count=total_count,
                    )
                )
                session.commit()

    def update_status(
        self,
        batch_id: str,
        status: str,
        *,
        started_at: dt.datetime | None = None,
        finished_at: dt.datetime | None = None,
    ) -> None:
        """Transition the batch status and optionally set timing columns."""
        with self._session_factory() as session:
            batch = session.get(Batch, batch_id)
            if batch is None:
                return
            batch.status = status
            if started_at is not None:
                batch.started_at = _to_naive_utc(started_at)
            if finished_at is not None:
                batch.finished_at = _to_naive_utc(finished_at)
            session.commit()

    def save_person_results(self, batch_id: str, results: list[PersonResult]) -> None:
        """Bulk-upsert per-person outcomes into ``batch_persons``.

        Uses ``merge`` so re-processing the same person in the same batch
        is idempotent (composite PK: batch_id + cedula).
        """
        with self._session_factory() as session:
            for r in results:
                session.merge(
                    BatchPerson(
                        batch_id=batch_id,
                        cedula=r.person_id,
                        result_status=r.status,
                        detail=r.detail or None,
                    )
                )
            session.commit()

    def save_report(self, batch_id: str, report: dict[str, Any]) -> None:
        """Store the JSON-serialised summary in the batch row."""
        with self._session_factory() as session:
            batch = session.get(Batch, batch_id)
            if batch is not None:
                batch.report = json.dumps(report, ensure_ascii=False)
                session.commit()
