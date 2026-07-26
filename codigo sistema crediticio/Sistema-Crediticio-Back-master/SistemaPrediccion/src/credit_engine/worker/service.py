"""Worker service assembly — the configured components the API layer uses.

Follows the same global-with-swap-point pattern as ``ingestion.queue``
(``get_queue`` / ``set_queue``): components are initialized eagerly at
import time (no lazy check-then-assign races under FastAPI's threadpool)
and each is replaceable through its Protocol.

Defaults (all local, zero infrastructure):
- repository: demo personas (``worker.demo``) — until ``database/`` lands
- engine: ``DemoOfferEngine`` — until ``engine/`` lands
- composer: ``DeliveryComposer(None)`` — template-only; call
  ``configure(composer=DeliveryComposer(MessageGenerator(OllamaClient())))``
  to turn on LLM messaging when Ollama is running
- outbox: ``InMemoryOutbox`` — until the persistent ``scheduled_messages``
  store lands (``scripts/create_database.sql``)
"""

from __future__ import annotations

from typing import Any

from credit_engine.ingestion.queue import BatchQueue, get_queue
from credit_engine.worker.composer import DeliveryComposer
from credit_engine.worker.contracts import MessageComposer, OfferEngine, OutboxStore, PersonRepository
from credit_engine.worker.demo import DemoOfferEngine, build_demo_repository
from credit_engine.worker.outbox import InMemoryOutbox
from credit_engine.worker.pipeline import PersonPipeline
from credit_engine.worker.processor import BatchProcessor

_repository: PersonRepository = build_demo_repository()
_engine: OfferEngine = DemoOfferEngine()
_composer: MessageComposer = DeliveryComposer(None)
_outbox: OutboxStore = InMemoryOutbox()
_batch_repository: Any = None


def get_outbox() -> OutboxStore:
    """The outbox where processed batches store their scheduled messages."""
    return _outbox


def get_repository() -> PersonRepository:
    """The person repository (demo or SQL-backed)."""
    return _repository


def get_engine() -> OfferEngine:
    """The offer engine (demo or ML-backed)."""
    return _engine


def get_processor(queue: BatchQueue | None = None) -> BatchProcessor:
    """Build a processor over the CURRENT components.

    Built per call (construction is trivial) so ``configure()`` and
    ``set_queue()`` swaps always take effect.

    Args:
        queue: The queue holding the batch. Callers that received a
            queue by injection (the API routes) MUST pass it through so
            the processor reads the same queue the batch was enqueued
            into — resolving ``get_queue()`` here again could diverge
            (e.g. under FastAPI ``dependency_overrides``) and silently
            never process the batch. Defaults to the global queue.
    """
    pipeline = PersonPipeline(
        repository=_repository,
        engine=_engine,
        composer=_composer,
        outbox=_outbox,
    )
    return BatchProcessor(
        queue if queue is not None else get_queue(),
        pipeline,
        batch_repository=_batch_repository,
    )


def configure(
    *,
    repository: PersonRepository | None = None,
    engine: OfferEngine | None = None,
    composer: MessageComposer | None = None,
    outbox: OutboxStore | None = None,
    batch_repository: Any = None,
) -> None:
    """Replace any subset of components (real database/engine, LLM composer)."""
    global _repository, _engine, _composer, _outbox, _batch_repository
    if repository is not None:
        _repository = repository
    if engine is not None:
        _engine = engine
    if composer is not None:
        _composer = composer
    if outbox is not None:
        _outbox = outbox
    if batch_repository is not None:
        _batch_repository = batch_repository


def reset_to_defaults() -> None:
    """Restore the default demo components (fresh outbox) — used by tests."""
    global _repository, _engine, _composer, _outbox, _batch_repository
    _repository = build_demo_repository()
    _engine = DemoOfferEngine()
    _composer = DeliveryComposer(None)
    _outbox = InMemoryOutbox()
    _batch_repository = None
