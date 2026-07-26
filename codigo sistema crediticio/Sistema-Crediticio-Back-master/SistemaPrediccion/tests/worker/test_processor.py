import pytest

from credit_engine.ingestion.queue import InMemoryBatchQueue
from credit_engine.worker.contracts import ComposedMessage
from credit_engine.worker.outbox import InMemoryOutbox
from credit_engine.worker.pipeline import PersonPipeline
from credit_engine.worker.processor import (
    BatchAlreadyProcessedError,
    BatchNotFoundError,
    BatchProcessor,
)
from credit_engine.worker.repository import InMemoryPersonRepository


class FakeEngine:
    def __init__(self, offers_by_person: dict):
        self.offers = offers_by_person

    def evaluate(self, person):
        return self.offers.get(person["id"])


class FakeComposer:
    def compose(self, offer):
        return ComposedMessage(text="msg", source="template")


class RecordingQueue(InMemoryBatchQueue):
    """Queue that records every status transition for assertions."""

    def __init__(self):
        super().__init__()
        self.transitions: list[str] = []

    def update_status(self, batch_id, status):
        self.transitions.append(status)
        return super().update_status(batch_id, status)


def _setup(person_ids, persons, offers_by_person):
    queue = RecordingQueue()
    batch = queue.enqueue(person_ids)
    repo = InMemoryPersonRepository(persons)
    pipeline = PersonPipeline(
        repository=repo,
        engine=FakeEngine(offers_by_person),
        composer=FakeComposer(),
        outbox=InMemoryOutbox(),
    )
    return queue, batch, BatchProcessor(queue, pipeline)


class TestProcessBatch:
    def test_unknown_batch_raises(self):
        queue = InMemoryBatchQueue()
        processor = BatchProcessor(queue, pipeline=None)

        with pytest.raises(BatchNotFoundError, match="not found"):
            processor.process_batch("nonexistent")

    def test_lifecycle_transitions_processing_then_completed(self, make_offer):
        persons = {"12345678": {"id": "12345678", "name": "Ana"}}
        offers = {"12345678": make_offer(person_id="12345678")}
        queue, batch, processor = _setup(["12345678"], persons, offers)

        processor.process_batch(batch.batch_id)

        assert queue.transitions == ["processing", "completed"]
        stored = queue.get_batch(batch.batch_id)
        assert stored.status == "completed"

    def test_report_counts_mixed_outcomes(self, make_offer):
        persons = {
            "11111111": {"id": "11111111", "name": "Ana"},
            "22222222": {"id": "22222222", "name": "Luis"},
        }
        offers = {"11111111": make_offer(person_id="11111111")}  # Luis: no offer
        queue, batch, processor = _setup(
            ["11111111", "22222222", "99999999"],  # 99999999 not in repo
            persons,
            offers,
        )

        report = processor.process_batch(batch.batch_id)

        assert report.total == 3
        assert report.processed == 1
        assert report.no_offer == 1
        assert report.person_not_found == 1
        assert report.errors == 0
        assert report.finished_at is not None

    def test_report_summary_stored_in_batch_metadata(self, make_offer):
        persons = {"12345678": {"id": "12345678", "name": "Ana"}}
        offers = {"12345678": make_offer(person_id="12345678")}
        queue, batch, processor = _setup(["12345678"], persons, offers)

        report = processor.process_batch(batch.batch_id)

        stored = queue.get_batch(batch.batch_id)
        assert stored.metadata["report"] == report.summary()
        assert stored.metadata["report"]["processed"] == 1

    def test_messages_are_stamped_with_batch_id(self, make_offer):
        queue = RecordingQueue()
        batch = queue.enqueue(["12345678"])
        outbox = InMemoryOutbox()
        pipeline = PersonPipeline(
            repository=InMemoryPersonRepository({"12345678": {"id": "12345678", "name": "Ana"}}),
            engine=FakeEngine({"12345678": make_offer(person_id="12345678")}),
            composer=FakeComposer(),
            outbox=outbox,
        )
        BatchProcessor(queue, pipeline).process_batch(batch.batch_id)

        messages = outbox.for_batch(batch.batch_id)
        assert len(messages) == 1
        assert messages[0].batch_id == batch.batch_id

    def test_per_person_failures_do_not_fail_batch(self):
        class ExplodingPipeline:
            def process_person(self, person_id, batch_id=""):
                from credit_engine.worker.contracts import PersonResult

                return PersonResult(person_id=person_id, status="error", detail="boom")

        queue = RecordingQueue()
        batch = queue.enqueue(["11111111", "22222222"])
        processor = BatchProcessor(queue, ExplodingPipeline())

        report = processor.process_batch(batch.batch_id)

        assert report.errors == 2
        assert queue.get_batch(batch.batch_id).status == "completed"

    def test_reprocessing_completed_batch_raises(self, make_offer):
        persons = {"12345678": {"id": "12345678", "name": "Ana"}}
        offers = {"12345678": make_offer(person_id="12345678")}
        queue, batch, processor = _setup(["12345678"], persons, offers)
        processor.process_batch(batch.batch_id)

        with pytest.raises(BatchAlreadyProcessedError, match="refusing to reprocess"):
            processor.process_batch(batch.batch_id)

        assert queue.transitions == ["processing", "completed"]

    def test_processing_batch_cannot_be_picked_up_twice(self, make_offer):
        persons = {"12345678": {"id": "12345678", "name": "Ana"}}
        offers = {"12345678": make_offer(person_id="12345678")}
        queue, batch, processor = _setup(["12345678"], persons, offers)
        queue.update_status(batch.batch_id, "processing")

        with pytest.raises(BatchAlreadyProcessedError):
            processor.process_batch(batch.batch_id)

    def test_report_is_stored_before_completed_status(self, make_offer):
        class AssertingQueue(RecordingQueue):
            """Fails if 'completed' is ever observable without its report."""

            def update_status(self, batch_id, status):
                if status == "completed":
                    assert "report" in self.get_batch(batch_id).metadata
                return super().update_status(batch_id, status)

        queue = AssertingQueue()
        batch = queue.enqueue(["12345678"])
        pipeline = PersonPipeline(
            repository=InMemoryPersonRepository({"12345678": {"id": "12345678", "name": "Ana"}}),
            engine=FakeEngine({"12345678": make_offer(person_id="12345678")}),
            composer=FakeComposer(),
            outbox=InMemoryOutbox(),
        )
        BatchProcessor(queue, pipeline).process_batch(batch.batch_id)

        assert queue.get_batch(batch.batch_id).status == "completed"

    def test_unexpected_crash_marks_batch_failed_and_reraises(self):
        class CrashingPipeline:
            def process_person(self, person_id, batch_id=""):
                raise MemoryError("out of memory")

        queue = RecordingQueue()
        batch = queue.enqueue(["11111111"])
        processor = BatchProcessor(queue, CrashingPipeline())

        with pytest.raises(MemoryError):
            processor.process_batch(batch.batch_id)

        assert queue.get_batch(batch.batch_id).status == "failed"
        assert queue.transitions == ["processing", "failed"]
