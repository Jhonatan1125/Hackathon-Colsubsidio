"""Data contracts and stage Protocols for the worker pipeline.

The worker orchestrates the per-person pipeline (``ROOT_IMPLEMENTATION.md``
§2.1: DB Lookup → ML Predict → LLM Generate → Scheduled Message Store) but
owns none of the stages — each one is injected behind a Protocol so the
worker runs today with local stand-ins and connects to the real
``database/`` and ``engine/`` packages when they land.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol

# ---------------------------------------------------------------------------
# The offer envelope (Decision Engine output)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Offer:
    """The offer envelope produced by the Decision Engine (Layer 3).

    Mirrors the upstream contract documented in ``llm/IMPLEMENTATION.md``
    ("Upstream Contract — The Offer Object"): every field is deterministic
    engine output; financial figures are display-ready COP strings so no
    downstream consumer ever re-computes or re-rounds them.

    This dataclass will migrate to ``engine/schemas/`` when the engine
    package lands (per ``ml/IMPLEMENTATION.md`` §3.3) — the worker will
    then import it instead of defining it.
    """

    person_id: str
    person_name: str
    product_id: str
    product_name: str
    amount_cop: str
    annual_rate_pct: str
    term_months: int
    cuota_cop: str
    channel: str
    contact_window: str
    trigger: str
    reason: str


# ---------------------------------------------------------------------------
# Pipeline result records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComposedMessage:
    """A ready-to-store message and how it was produced.

    ``source`` is ``"llm"`` when the LLM rephrased the offer, or
    ``"template"`` when the deterministic fallback rendered it
    (graceful degradation per ``llm/IMPLEMENTATION.md``).
    """

    text: str
    source: str


@dataclass(frozen=True)
class ScheduledMessage:
    """Outbox record: what, who, when, where, and the message itself.

    Field set follows the Scheduled Message Store of
    ``ROOT_IMPLEMENTATION.md`` §2.1/§7.3 (``scheduled_messages``).
    """

    person_id: str
    product_id: str
    channel: str
    contact_window: str
    trigger: str
    message_text: str
    message_source: str
    batch_id: str = ""
    status: str = "scheduled"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    amount_cop: Decimal | None = None
    annual_rate_pct: Decimal | None = None
    term_months: int | None = None
    cuota_cop: Decimal | None = None


def _cop_display_to_decimal(value: str) -> Decimal | None:
    """Parse a COP display string like '$5.600.000' into Decimal('5600000')."""
    try:
        cleaned = value.replace("$", "").replace(".", "")
        return Decimal(cleaned)
    except (ValueError, AttributeError):
        return None


def _rate_display_to_decimal(value: str) -> Decimal | None:
    """Parse a rate display string like '14,5% E.A.' into Decimal('14.5')."""
    try:
        cleaned = value.replace("%", "").replace(" E.A.", "").replace(",", ".")
        return Decimal(cleaned)
    except (ValueError, AttributeError):
        return None


@dataclass(frozen=True)
class PersonResult:
    """Outcome of processing one person ID within a batch.

    ``status`` is one of:
    - ``"processed"`` — offer generated, message stored in the outbox
    - ``"person_not_found"`` — ID not present in the person repository
    - ``"no_offer"`` — engine declined (e.g. PD gate, no positive-EV product)
    - ``"error"`` — unexpected failure in any stage (detail preserved)
    """

    person_id: str
    status: str
    detail: str = ""


@dataclass(frozen=True)
class BatchReport:
    """Summary of one processed batch."""

    batch_id: str
    total: int
    processed: int
    person_not_found: int
    no_offer: int
    errors: int
    results: list[PersonResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    def summary(self) -> dict[str, Any]:
        """Compact dict for storage in batch metadata / API exposure."""
        return {
            "total": self.total,
            "processed": self.processed,
            "person_not_found": self.person_not_found,
            "no_offer": self.no_offer,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Stage Protocols (structural contracts — no inheritance required)
# ---------------------------------------------------------------------------


class PersonRepository(Protocol):
    """Person lookup — DB Lookup stage.

    Fulfilled today by ``worker.repository.InMemoryPersonRepository``;
    fulfilled later by the ``database/`` package (synthetic population
    or real member records).
    """

    def get_person(self, person_id: str) -> dict[str, Any] | None: ...


class OfferEngine(Protocol):
    """Offer evaluation — ML Predict + NBO decision stage.

    Fulfilled later by the ``engine/`` package (which consumes the
    ``ml/`` predictor probabilities and runs PD gate → eligibility →
    EV ranking → channel scoring → SHAP reasoning). Returns ``None``
    when no offer should be made (risk gate or no positive-EV product).
    """

    def evaluate(self, person: dict[str, Any]) -> Offer | None: ...


class MessageComposer(Protocol):
    """Message composition — LLM Generate stage with fallback.

    Fulfilled by ``worker.composer.DeliveryComposer`` (llm module +
    deterministic templates).
    """

    def compose(self, offer: Offer) -> ComposedMessage: ...


class OutboxStore(Protocol):
    """Scheduled message persistence — outbox stage.

    Fulfilled today by ``worker.outbox.InMemoryOutbox``; fulfilled later
    by the persistent ``scheduled_messages`` store (SQL Server DDL in
    ``scripts/create_database.sql``, per ``ROOT_IMPLEMENTATION.md`` §7.3)
    owned by ``database/``/``dispatcher/``. ``for_person`` and
    ``for_batch`` are the read surfaces the API and the future
    dispatcher use (mirroring the DDL's person/batch indexes).
    """

    def save(self, message: ScheduledMessage) -> None: ...

    def for_person(self, person_id: str) -> list[ScheduledMessage]: ...

    def for_batch(self, batch_id: str) -> list[ScheduledMessage]: ...
