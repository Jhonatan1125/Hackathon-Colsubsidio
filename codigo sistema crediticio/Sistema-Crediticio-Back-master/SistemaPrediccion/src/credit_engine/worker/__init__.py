"""Worker package — async batch orchestration of the per-person pipeline.

Runtime flow (``ROOT_IMPLEMENTATION.md`` §2.1):

    ingestion queue (batch) → BatchProcessor → per person:
        PersonRepository.get_person   (DB Lookup — database/ stand-in)
        OfferEngine.evaluate          (ML Predict + NBO — engine/ later)
        MessageComposer.compose       (LLM Generate + template fallback)
        OutboxStore.save              (Scheduled Message Store stand-in)

Assemble one with local stand-ins::

    from credit_engine.ingestion.queue import get_queue
    from credit_engine.worker import (
        BatchProcessor, DeliveryComposer, InMemoryOutbox,
        InMemoryPersonRepository, PersonPipeline, WorkerRunner,
    )

    pipeline = PersonPipeline(
        repository=InMemoryPersonRepository(),
        engine=my_engine,                    # any OfferEngine implementation
        composer=DeliveryComposer(),         # template-only without an LLM client
        outbox=InMemoryOutbox(),
    )
    runner = WorkerRunner(BatchProcessor(get_queue(), pipeline))
    future = runner.submit(batch_id)
"""

from credit_engine.worker.composer import LLM_CHANNELS, DeliveryComposer, TextGenerator
from credit_engine.worker.demo import DEMO_PERSONS, DemoOfferEngine, build_demo_repository
from credit_engine.worker.contracts import (
    BatchReport,
    ComposedMessage,
    MessageComposer,
    Offer,
    OfferEngine,
    OutboxStore,
    PersonRepository,
    PersonResult,
    ScheduledMessage,
)
from credit_engine.worker.outbox import InMemoryOutbox
from credit_engine.worker.pipeline import PersonPipeline
from credit_engine.worker.processor import (
    BatchAlreadyProcessedError,
    BatchNotFoundError,
    BatchProcessor,
)
from credit_engine.worker.repository import InMemoryPersonRepository
from credit_engine.worker.runner import WorkerRunner
from credit_engine.worker.service import configure, get_outbox, get_processor, reset_to_defaults

__all__ = [
    "Offer",
    "ComposedMessage",
    "ScheduledMessage",
    "PersonResult",
    "BatchReport",
    "PersonRepository",
    "OfferEngine",
    "MessageComposer",
    "OutboxStore",
    "TextGenerator",
    "DeliveryComposer",
    "LLM_CHANNELS",
    "InMemoryPersonRepository",
    "InMemoryOutbox",
    "PersonPipeline",
    "BatchProcessor",
    "BatchNotFoundError",
    "BatchAlreadyProcessedError",
    "WorkerRunner",
    "DemoOfferEngine",
    "DEMO_PERSONS",
    "build_demo_repository",
    "get_outbox",
    "get_processor",
    "configure",
    "reset_to_defaults",
]
