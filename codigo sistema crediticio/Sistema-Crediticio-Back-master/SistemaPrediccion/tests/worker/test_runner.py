from credit_engine.ingestion.queue import InMemoryBatchQueue
from credit_engine.worker.contracts import ComposedMessage
from credit_engine.worker.outbox import InMemoryOutbox
from credit_engine.worker.pipeline import PersonPipeline
from credit_engine.worker.processor import BatchProcessor
from credit_engine.worker.repository import InMemoryPersonRepository
from credit_engine.worker.runner import WorkerRunner


class FakeEngine:
    def __init__(self, offer):
        self.offer = offer

    def evaluate(self, person):
        return self.offer


class FakeComposer:
    def compose(self, offer):
        return ComposedMessage(text="msg", source="template")


class TestWorkerRunner:
    def test_submit_processes_batch_in_background(self, make_offer):
        queue = InMemoryBatchQueue()
        batch = queue.enqueue(["12345678"])
        pipeline = PersonPipeline(
            repository=InMemoryPersonRepository({"12345678": {"name": "Ana"}}),
            engine=FakeEngine(make_offer(person_id="12345678")),
            composer=FakeComposer(),
            outbox=InMemoryOutbox(),
        )
        runner = WorkerRunner(BatchProcessor(queue, pipeline))
        try:
            future = runner.submit(batch.batch_id)
            report = future.result(timeout=10)
        finally:
            runner.shutdown()

        assert report.processed == 1
        assert queue.get_batch(batch.batch_id).status == "completed"

    def test_future_surfaces_processor_errors(self):
        queue = InMemoryBatchQueue()
        runner = WorkerRunner(BatchProcessor(queue, pipeline=None))
        try:
            future = runner.submit("nonexistent")
            exc = future.exception(timeout=10)
        finally:
            runner.shutdown()

        assert exc is not None
        assert "not found" in str(exc)
