from credit_engine.worker.contracts import ScheduledMessage
from credit_engine.worker.outbox import InMemoryOutbox
from credit_engine.worker.repository import InMemoryPersonRepository


def _message(person_id: str = "P001", batch_id: str = "batch-1") -> ScheduledMessage:
    return ScheduledMessage(
        person_id=person_id,
        product_id="educativo",
        channel="whatsapp",
        contact_window="night",
        trigger="immediate",
        message_text="hola",
        message_source="template",
        batch_id=batch_id,
    )


class TestInMemoryPersonRepository:
    def test_returns_none_for_unknown_person(self):
        repo = InMemoryPersonRepository()
        assert repo.get_person("unknown") is None

    def test_add_and_get_person(self):
        repo = InMemoryPersonRepository()
        repo.add_person("12345678", {"name": "Ana"})
        assert repo.get_person("12345678") == {"name": "Ana"}

    def test_constructor_seed(self):
        repo = InMemoryPersonRepository({"P001": {"name": "Luis"}})
        assert repo.get_person("P001") == {"name": "Luis"}

    def test_get_returns_copy(self):
        repo = InMemoryPersonRepository({"P001": {"name": "Luis"}})
        record = repo.get_person("P001")
        record["name"] = "mutated"
        assert repo.get_person("P001") == {"name": "Luis"}

    def test_constructor_copies_seed_dict(self):
        seed = {"P001": {"name": "Luis"}}
        repo = InMemoryPersonRepository(seed)
        seed["P002"] = {"name": "Eva"}
        assert repo.get_person("P002") is None


class TestInMemoryOutbox:
    def test_starts_empty(self):
        assert InMemoryOutbox().all_messages() == []

    def test_save_and_list(self):
        outbox = InMemoryOutbox()
        msg = _message()
        outbox.save(msg)
        assert outbox.all_messages() == [msg]

    def test_for_person_filters(self):
        outbox = InMemoryOutbox()
        outbox.save(_message("P001"))
        outbox.save(_message("P002"))
        outbox.save(_message("P001"))
        assert len(outbox.for_person("P001")) == 2
        assert len(outbox.for_person("P002")) == 1

    def test_for_batch_filters(self):
        outbox = InMemoryOutbox()
        outbox.save(_message("P001", batch_id="batch-A"))
        outbox.save(_message("P001", batch_id="batch-B"))
        outbox.save(_message("P002", batch_id="batch-A"))
        assert len(outbox.for_batch("batch-A")) == 2
        assert len(outbox.for_batch("batch-B")) == 1
        assert outbox.for_batch("batch-C") == []

    def test_all_messages_returns_copy(self):
        outbox = InMemoryOutbox()
        outbox.save(_message())
        listed = outbox.all_messages()
        listed.clear()
        assert len(outbox.all_messages()) == 1

    def test_default_status_is_scheduled(self):
        assert _message().status == "scheduled"
