import uuid
from datetime import UTC, datetime

import pytest

from credit_engine.ingestion.queue import (
    VALID_STATUSES,
    BatchResult,
    InMemoryBatchQueue,
    enqueue_batch,
    get_queue,
    set_queue,
)


class TestBatchResult:
    def test_creates_with_defaults(self):
        result = BatchResult(batch_id="abc", status="queued", count=0)
        assert result.batch_id == "abc"
        assert result.status == "queued"
        assert result.count == 0
        assert result.person_ids == []
        assert isinstance(result.created_at, datetime)
        assert result.created_at.tzinfo == UTC

    def test_stores_person_ids(self):
        ids = ["12345", "67890"]
        result = BatchResult(batch_id="abc", status="queued", count=2, person_ids=ids)
        assert result.person_ids == ids
        assert result.count == 2

    def test_created_at_is_utc(self):
        result = BatchResult(batch_id="abc", status="queued", count=0)
        assert result.created_at.tzinfo == UTC


class TestInMemoryBatchQueue:
    def test_enqueue_returns_batch_result(self):
        queue = InMemoryBatchQueue()
        result = queue.enqueue(["12345", "67890"])
        assert isinstance(result, BatchResult)
        assert result.status == "queued"
        assert result.count == 2

    def test_enqueue_generates_unique_batch_ids(self):
        queue = InMemoryBatchQueue()
        result1 = queue.enqueue(["12345"])
        result2 = queue.enqueue(["67890"])
        assert result1.batch_id != result2.batch_id
        uuid.UUID(result1.batch_id)  # should not raise
        uuid.UUID(result2.batch_id)  # should not raise

    def test_enqueue_stores_person_ids_copy(self):
        queue = InMemoryBatchQueue()
        ids = ["12345", "67890"]
        result = queue.enqueue(ids)
        ids.append("99999")
        assert result.person_ids == ["12345", "67890"]

    def test_get_batch_returns_enqueued_batch(self):
        queue = InMemoryBatchQueue()
        created = queue.enqueue(["12345"])
        retrieved = queue.get_batch(created.batch_id)
        assert retrieved is not None
        assert retrieved.batch_id == created.batch_id
        assert retrieved.person_ids == ["12345"]

    def test_get_batch_returns_none_for_unknown_id(self):
        queue = InMemoryBatchQueue()
        assert queue.get_batch("nonexistent") is None

    def test_enqueue_handles_empty_list(self):
        queue = InMemoryBatchQueue()
        result = queue.enqueue([])
        assert result.count == 0
        assert result.person_ids == []

    def test_metadata_is_stored(self):
        queue = InMemoryBatchQueue()
        result = queue.enqueue(["12345"], metadata={"source": "test"})
        assert result.status == "queued"
        assert result.metadata == {"source": "test"}

    def test_metadata_defaults_to_empty_dict(self):
        queue = InMemoryBatchQueue()
        result = queue.enqueue(["12345"])
        assert result.metadata == {}

    def test_metadata_is_stored_as_copy(self):
        queue = InMemoryBatchQueue()
        meta = {"source": "test"}
        result = queue.enqueue(["12345"], metadata=meta)
        meta["source"] = "mutated"
        assert result.metadata == {"source": "test"}


class TestUpdateStatus:
    def test_transitions_to_processing(self):
        queue = InMemoryBatchQueue()
        created = queue.enqueue(["12345"])
        updated = queue.update_status(created.batch_id, "processing")
        assert updated is not None
        assert updated.status == "processing"
        retrieved = queue.get_batch(created.batch_id)
        assert retrieved is not None
        assert retrieved.status == "processing"

    def test_full_lifecycle(self):
        queue = InMemoryBatchQueue()
        created = queue.enqueue(["12345"])
        queue.update_status(created.batch_id, "processing")
        final = queue.update_status(created.batch_id, "completed")
        assert final is not None
        assert final.status == "completed"

    def test_unknown_batch_returns_none(self):
        queue = InMemoryBatchQueue()
        assert queue.update_status("nonexistent", "processing") is None

    def test_invalid_status_raises_value_error(self):
        queue = InMemoryBatchQueue()
        created = queue.enqueue(["12345"])
        with pytest.raises(ValueError, match="Unknown status"):
            queue.update_status(created.batch_id, "banana")

    def test_valid_statuses_cover_lifecycle(self):
        assert VALID_STATUSES == ("queued", "processing", "completed", "failed")


class TestGlobalQueue:
    def test_get_queue_returns_same_instance(self):
        queue = InMemoryBatchQueue()
        try:
            set_queue(queue)
            assert get_queue() is queue
        finally:
            set_queue(InMemoryBatchQueue())

    def test_set_queue_replaces_global(self):
        old = get_queue()
        new_queue = InMemoryBatchQueue()
        try:
            set_queue(new_queue)
            assert get_queue() is new_queue
            assert get_queue() is not old
        finally:
            set_queue(InMemoryBatchQueue())

    def test_enqueue_batch_uses_default_queue(self):
        default = get_queue()
        result = enqueue_batch(["12345"])
        retrieved = default.get_batch(result.batch_id)
        assert retrieved is not None
        assert retrieved.person_ids == ["12345"]

    def test_enqueue_batch_uses_explicit_queue(self):
        queue1 = InMemoryBatchQueue()
        queue2 = InMemoryBatchQueue()
        result = enqueue_batch(["12345"], queue=queue1)
        assert queue1.get_batch(result.batch_id) is not None
        assert queue2.get_batch(result.batch_id) is None


class TestQueueIsolation:
    def test_queues_are_independent(self):
        q1 = InMemoryBatchQueue()
        q2 = InMemoryBatchQueue()
        r1 = q1.enqueue(["11111"])
        r2 = q2.enqueue(["22222"])
        assert q1.get_batch(r2.batch_id) is None
        assert q2.get_batch(r1.batch_id) is None
