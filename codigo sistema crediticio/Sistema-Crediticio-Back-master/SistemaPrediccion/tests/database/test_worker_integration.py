"""End-to-end: the worker pipeline running over the real database layer.

Proves the Protocol swap works — the same PersonPipeline that runs on
in-memory stand-ins runs unchanged on SqlPersonRepository + SqlOutbox.
"""

from credit_engine.database.repositories import SqlOutbox, SqlPersonRepository
from credit_engine.ingestion.queue import InMemoryBatchQueue
from credit_engine.worker.composer import DeliveryComposer
from credit_engine.worker.demo import DEMO_PERSONS, DemoOfferEngine
from credit_engine.worker.pipeline import PersonPipeline
from credit_engine.worker.processor import BatchProcessor


def _build_processor(session_factory):
    repo = SqlPersonRepository(session_factory)
    for persona in DEMO_PERSONS.values():
        repo.save_person(persona)

    queue = InMemoryBatchQueue()
    pipeline = PersonPipeline(
        repository=repo,
        engine=DemoOfferEngine(),
        composer=DeliveryComposer(None),
        outbox=SqlOutbox(session_factory),
    )
    return queue, BatchProcessor(queue, pipeline), SqlOutbox(session_factory)


class TestPipelineOverDatabase:
    def test_batch_processes_end_to_end_on_sql(self, session_factory):
        queue, processor, outbox = _build_processor(session_factory)
        batch = queue.enqueue(list(DEMO_PERSONS))

        report = processor.process_batch(batch.batch_id)

        assert report.processed == 11
        assert report.no_offer == 1  # mora 90_MAS_DIAS declined
        assert report.errors == 0

        messages = outbox.for_batch(batch.batch_id)
        assert len(messages) == 11
        maria = next(m for m in messages if m.person_id == "10000001")
        assert maria.product_id == "educativo"
        assert maria.channel == "whatsapp"
        assert "$" in maria.message_text

    def test_unknown_persons_reported_not_found(self, session_factory):
        queue, processor, outbox = _build_processor(session_factory)
        batch = queue.enqueue(["88888888", "77777777"])

        report = processor.process_batch(batch.batch_id)

        assert report.person_not_found == 2
        assert outbox.for_batch(batch.batch_id) == []
