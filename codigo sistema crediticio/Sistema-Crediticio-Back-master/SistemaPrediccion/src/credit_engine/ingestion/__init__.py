"""Ingestion package — ID validation, file parsing, and batch queuing.

Entry gate of the system pipeline (``ROOT_IMPLEMENTATION.md`` §2.1):
Input (CSV / TXT / API) → parse → validate → enqueue → worker pipeline.
"""

from credit_engine.ingestion.parser import parse_csv, parse_txt
from credit_engine.ingestion.queue import (
    VALID_STATUSES,
    BatchQueue,
    BatchResult,
    InMemoryBatchQueue,
    enqueue_batch,
    get_queue,
    set_queue,
)
from credit_engine.ingestion.validator import (
    MAX_BATCH_SIZE,
    MIN_BATCH_SIZE,
    ValidationResult,
    is_valid_person_id,
    validate_person_ids,
)

__all__ = [
    "parse_csv",
    "parse_txt",
    "validate_person_ids",
    "is_valid_person_id",
    "ValidationResult",
    "MIN_BATCH_SIZE",
    "MAX_BATCH_SIZE",
    "enqueue_batch",
    "get_queue",
    "set_queue",
    "BatchQueue",
    "BatchResult",
    "InMemoryBatchQueue",
    "VALID_STATUSES",
]
