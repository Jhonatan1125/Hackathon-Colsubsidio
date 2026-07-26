"""Batch processor: drives one batch through the queue lifecycle.

The processor is the single writer of batch statuses (the lifecycle the
ingestion module defines: ``queued → processing → completed | failed``)
and the producer of the ``BatchReport`` summary, which it also stores in
the batch's metadata so status queries can expose it.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from credit_engine.ingestion.queue import BatchQueue
from credit_engine.worker.contracts import BatchReport, PersonResult
from credit_engine.worker.pipeline import PersonPipeline

logger = logging.getLogger(__name__)


class BatchNotFoundError(Exception):
    """Raised when the requested batch ID does not exist in the queue."""


class BatchAlreadyProcessedError(Exception):
    """Raised when a batch has already left the ``queued`` state.

    Guards against double-processing (API retries, duplicate submits):
    reprocessing would store duplicate scheduled messages and message
    the same customers twice.
    """


class BatchProcessor:
    """Processes queued batches person-by-person and reports the outcome."""

    def __init__(
        self,
        queue: BatchQueue,
        pipeline: PersonPipeline,
        batch_repository: Any = None,
    ) -> None:
        self._queue = queue
        self._pipeline = pipeline
        self._batch_repo = batch_repository

    def process_batch(self, batch_id: str) -> BatchReport:
        """Run the full pipeline for every person in the batch.

        Per-person failures are recorded and never abort the batch —
        the batch finishes ``completed`` with the mix of outcomes in its
        report. The batch is marked ``failed`` only when the processor
        itself crashes unexpectedly (the exception is re-raised after
        the status update so callers see the real error).

        Raises:
            BatchNotFoundError: If ``batch_id`` is not in the queue.
            BatchAlreadyProcessedError: If the batch is not in the
                ``queued`` state (already processing, completed, or failed).
        """
        start = time.time()
        batch = self._queue.get_batch(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} not found in queue")
        if batch.status != "queued":
            raise BatchAlreadyProcessedError(
                f"Batch {batch_id} is '{batch.status}', expected 'queued' — refusing to reprocess"
            )

        logger.info("Processing batch %s — %d person(s)", batch_id, batch.count)
        started_at = datetime.now(UTC)

        if self._batch_repo is not None:
            self._batch_repo.create_batch(batch_id, batch.count)
            self._batch_repo.update_status(batch_id, "processing", started_at=started_at)

        self._queue.update_status(batch_id, "processing")

        results: list[PersonResult] = []
        try:
            for idx, person_id in enumerate(batch.person_ids, start=1):
                logger.debug("Batch %s — processing person %d/%d: %s", batch_id, idx, batch.count, person_id)
                person_start = time.time()
                result = self._pipeline.process_person(person_id, batch_id)
                person_elapsed = time.time() - person_start
                logger.debug(
                    "Batch %s — person %d/%d %s: %s (%.3fs)",
                    batch_id, idx, batch.count, person_id, result.status, person_elapsed,
                )
                results.append(result)
        except Exception as exc:
            logger.exception("Batch %s — unexpected error during processing: %s", batch_id, exc)
            self._queue.update_status(batch_id, "failed")
            if self._batch_repo is not None:
                self._batch_repo.update_status(batch_id, "failed")
            raise

        report = BatchReport(
            batch_id=batch_id,
            total=len(results),
            processed=sum(1 for r in results if r.status == "processed"),
            person_not_found=sum(1 for r in results if r.status == "person_not_found"),
            no_offer=sum(1 for r in results if r.status == "no_offer"),
            errors=sum(1 for r in results if r.status == "error"),
            results=results,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )

        elapsed = time.time() - start
        logger.info(
            "Batch %s completed in %.3fs — processed: %d, not_found: %d, no_offer: %d, errors: %d",
            batch_id, elapsed, report.processed, report.person_not_found, report.no_offer, report.errors,
        )

        if self._batch_repo is not None:
            self._batch_repo.save_person_results(batch_id, results)
            self._batch_repo.save_report(batch_id, report.summary())

        # Store the report BEFORE the terminal status so "completed" is never
        # observable without its report (the API polls status from another
        # thread). Note: writing through the returned object is an in-memory
        # queue convenience, not part of the BatchQueue Protocol — see the
        # module plan's Open Questions for the Redis/SQS implication.
        batch.metadata["report"] = report.summary()
        self._queue.update_status(batch_id, "completed")

        if self._batch_repo is not None:
            self._batch_repo.update_status(batch_id, "completed", finished_at=report.finished_at)

        return report
