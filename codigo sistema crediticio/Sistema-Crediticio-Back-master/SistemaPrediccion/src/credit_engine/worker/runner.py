"""Background execution of batch processing.

``ROOT_IMPLEMENTATION.md`` §8: the campaign processor handles batches
"asynchronously in background threads, returning job tracking IDs". The
runner wraps a thread pool around the ``BatchProcessor``; the batch ID
is the tracking ID and the queue holds the observable status.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from credit_engine.worker.contracts import BatchReport
from credit_engine.worker.processor import BatchProcessor


class WorkerRunner:
    """Runs batch processing on background threads.

    Args:
        processor: The batch processor to execute.
        max_workers: Concurrent batches. Defaults to 1 — the in-memory
            queue and stores are not synchronized for concurrent batch
            writes, and single-worker keeps ordering deterministic.
    """

    def __init__(self, processor: BatchProcessor, max_workers: int = 1) -> None:
        self._processor = processor
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="credit-worker")

    def submit(self, batch_id: str) -> Future[BatchReport]:
        """Schedule a batch for background processing.

        Returns the Future immediately; the queue's batch status is the
        polling surface (``GET /api/v1/batches/{batch_id}``), the Future
        is for callers that hold a reference (tests, scripts).
        """
        return self._executor.submit(self._processor.process_batch, batch_id)

    def shutdown(self, wait: bool = True) -> None:
        """Stop accepting work and optionally wait for running batches."""
        self._executor.shutdown(wait=wait)
