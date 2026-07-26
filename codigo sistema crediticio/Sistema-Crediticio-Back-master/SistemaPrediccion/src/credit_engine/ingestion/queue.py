"""In-memory batch queue for managing submitted person ID batches.

This is the local stand-in for the Message Queue of the system pipeline
(``ROOT_IMPLEMENTATION.md`` §2.1: SQS or Redis Queue). The ``BatchQueue``
Protocol is the swap point: a Redis/SQS-backed implementation plugs in
via ``set_queue()`` without touching the API layer or the worker.

Batch lifecycle (transitions owned by the worker pipeline):
``queued`` → ``processing`` → ``completed`` | ``failed``
"""

import logging
import uuid
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
from datetime import UTC, datetime
from typing import Any, Protocol

VALID_STATUSES: tuple[str, ...] = ("queued", "processing", "completed", "failed")


@dataclass
class BatchResult:
    """Result of enqueuing a batch of person IDs.

    Attributes:
        batch_id: Unique identifier for the batch.
        status: Current processing status (one of ``VALID_STATUSES``).
        count: Number of valid person IDs in the batch.
        person_ids: The list of validated person IDs.
        created_at: UTC timestamp when the batch was created.
        metadata: Optional caller-supplied context (e.g. source filename).
    """

    batch_id: str
    status: str
    count: int
    person_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class BatchQueue(Protocol):
    """Protocol defining the batch queue interface."""

    def enqueue(self, person_ids: list[str], metadata: dict[str, Any] | None = None) -> BatchResult: ...

    def get_batch(self, batch_id: str) -> BatchResult | None: ...

    def update_status(self, batch_id: str, status: str) -> BatchResult | None: ...


class InMemoryBatchQueue:
    """In-memory implementation of BatchQueue backed by a dictionary.

    This queue is process-local. With uvicorn --workers N, each worker
    has its own copy; batches enqueued by one worker are invisible to
    others. Use a single worker (default), or swap in a Redis-backed
    queue via set_queue().
    """

    def __init__(self) -> None:
        self._batches: dict[str, BatchResult] = {}

    def enqueue(self, person_ids: list[str], metadata: dict[str, Any] | None = None) -> BatchResult:
        """Store a new batch and return its result.

        Args:
            person_ids: Validated person IDs to enqueue.
            metadata: Optional metadata dictionary stored with the batch.

        Returns:
            BatchResult with a generated UUID batch ID and "queued" status.
        """
        batch_id = str(uuid.uuid4())
        result = BatchResult(
            batch_id=batch_id,
            status="queued",
            count=len(person_ids),
            person_ids=list(person_ids),
            created_at=datetime.now(UTC),
            metadata=dict(metadata) if metadata else {},
        )
        self._batches[batch_id] = result
        logger.info("Batch %s enqueued — %d person(s),  metadata keys: %s", batch_id, len(person_ids), list(metadata.keys()) if metadata else "none")
        return result

    def get_batch(self, batch_id: str) -> BatchResult | None:
        """Retrieve a batch by its ID.

        Args:
            batch_id: The UUID string identifying the batch.

        Returns:
            The BatchResult if found, or None.
        """
        return self._batches.get(batch_id)

    def update_status(self, batch_id: str, status: str) -> BatchResult | None:
        """Transition a batch to a new lifecycle status.

        Intended for the worker pipeline: it marks batches as
        "processing" when picked up and "completed"/"failed" when done.

        Args:
            batch_id: The UUID string identifying the batch.
            status: New status — one of ``VALID_STATUSES``.

        Returns:
            The updated BatchResult, or None if the batch does not exist.

        Raises:
            ValueError: If ``status`` is not a recognised lifecycle status.
        """
        if status not in VALID_STATUSES:
            logger.error("Attempted to set unknown status '%s' for batch %s", status, batch_id)
            raise ValueError(f"Unknown status '{status}'. Valid statuses: {', '.join(VALID_STATUSES)}")

        batch = self._batches.get(batch_id)
        if batch is None:
            logger.warning("Batch %s not found for status update to %s", batch_id, status)
            return None

        previous = batch.status
        batch.status = status
        logger.info("Batch %s status: %s → %s", batch_id, previous, status)
        return batch


_default_queue: BatchQueue = InMemoryBatchQueue()


def get_queue() -> BatchQueue:
    """Return the global batch queue.

    Initialized eagerly at import time: lazy check-then-assign here would
    race under FastAPI's threadpool (concurrent first requests could each
    build their own queue, silently orphaning accepted batches).
    """
    return _default_queue


def set_queue(queue: BatchQueue) -> None:
    """Replace the global batch queue (useful for testing or Redis-backed queues)."""
    global _default_queue
    _default_queue = queue


def enqueue_batch(
    person_ids: list[str],
    *,
    metadata: dict[str, Any] | None = None,
    queue: BatchQueue | None = None,
) -> BatchResult:
    """Enqueue a batch of person IDs using the given or default queue.

    Args:
        person_ids: Validated person IDs to enqueue.
        metadata: Optional metadata for the batch.
        queue: Explicit queue to use; falls back to the global default.

    Returns:
        BatchResult for the newly enqueued batch.
    """
    q = queue or get_queue()
    return q.enqueue(person_ids, metadata=metadata)
