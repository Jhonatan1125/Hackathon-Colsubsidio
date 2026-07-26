from credit_engine.worker.contracts import ComposedMessage
from credit_engine.worker.outbox import InMemoryOutbox
from credit_engine.worker.pipeline import PersonPipeline
from credit_engine.worker.repository import InMemoryPersonRepository


class FakeEngine:
    def __init__(self, offer=None, exc: Exception | None = None):
        self.offer = offer
        self.exc = exc

    def evaluate(self, person):
        if self.exc is not None:
            raise self.exc
        return self.offer


class FakeComposer:
    def __init__(self, exc: Exception | None = None):
        self.exc = exc

    def compose(self, offer):
        if self.exc is not None:
            raise self.exc
        return ComposedMessage(text=f"msg for {offer.person_id}", source="template")


class FailingOutbox:
    def save(self, message):
        raise RuntimeError("disk full")


def _pipeline(repository=None, engine=None, composer=None, outbox=None):
    return PersonPipeline(
        repository=repository or InMemoryPersonRepository(),
        engine=engine or FakeEngine(),
        composer=composer or FakeComposer(),
        outbox=outbox or InMemoryOutbox(),
    )


class TestHappyPath:
    def test_processes_person_and_stores_message(self, make_offer):
        repo = InMemoryPersonRepository({"P00123": {"name": "María"}})
        outbox = InMemoryOutbox()
        offer = make_offer()
        pipeline = _pipeline(repository=repo, engine=FakeEngine(offer=offer), outbox=outbox)

        result = pipeline.process_person("P00123")

        assert result.status == "processed"
        assert result.detail == "template"
        messages = outbox.all_messages()
        assert len(messages) == 1
        stored = messages[0]
        assert stored.person_id == "P00123"
        assert stored.product_id == offer.product_id
        assert stored.channel == offer.channel
        assert stored.contact_window == offer.contact_window
        assert stored.trigger == offer.trigger
        assert stored.message_source == "template"
        assert stored.status == "scheduled"


class TestShortCircuits:
    def test_person_not_found(self):
        pipeline = _pipeline(repository=InMemoryPersonRepository())

        result = pipeline.process_person("99999999")

        assert result.status == "person_not_found"

    def test_no_offer_when_engine_declines(self):
        repo = InMemoryPersonRepository({"12345678": {"name": "Carlos"}})
        outbox = InMemoryOutbox()
        pipeline = _pipeline(repository=repo, engine=FakeEngine(offer=None), outbox=outbox)

        result = pipeline.process_person("12345678")

        assert result.status == "no_offer"
        assert outbox.all_messages() == []


class TestErrorIsolation:
    def test_engine_exception_becomes_error_result(self):
        repo = InMemoryPersonRepository({"12345678": {"name": "Carlos"}})
        pipeline = _pipeline(repository=repo, engine=FakeEngine(exc=RuntimeError("model missing")))

        result = pipeline.process_person("12345678")

        assert result.status == "error"
        assert "RuntimeError" in result.detail
        assert "model missing" in result.detail

    def test_composer_exception_becomes_error_result(self, make_offer):
        repo = InMemoryPersonRepository({"12345678": {"name": "Carlos"}})
        pipeline = _pipeline(
            repository=repo,
            engine=FakeEngine(offer=make_offer()),
            composer=FakeComposer(exc=ValueError("bad channel")),
        )

        result = pipeline.process_person("12345678")

        assert result.status == "error"
        assert "ValueError" in result.detail

    def test_outbox_exception_becomes_error_result(self, make_offer):
        repo = InMemoryPersonRepository({"12345678": {"name": "Carlos"}})
        pipeline = _pipeline(
            repository=repo,
            engine=FakeEngine(offer=make_offer()),
            outbox=FailingOutbox(),
        )

        result = pipeline.process_person("12345678")

        assert result.status == "error"
        assert "disk full" in result.detail

    def test_never_raises(self):
        class ExplodingRepo:
            def get_person(self, person_id):
                raise ConnectionError("db down")

        pipeline = _pipeline(repository=ExplodingRepo())

        result = pipeline.process_person("12345678")

        assert result.status == "error"
        assert "ConnectionError" in result.detail
