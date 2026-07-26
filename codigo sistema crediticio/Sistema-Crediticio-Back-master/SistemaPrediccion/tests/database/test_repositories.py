from credit_engine.database.repositories import SqlOutbox, SqlPersonRepository
from credit_engine.worker.contracts import ScheduledMessage
from credit_engine.worker.demo import DEMO_PERSONS


def _maria() -> dict:
    return dict(DEMO_PERSONS["10000001"])


def _message(person_id: str = "10000001", batch_id: str = "batch-A") -> ScheduledMessage:
    return ScheduledMessage(
        person_id=person_id,
        product_id="educativo",
        channel="whatsapp",
        contact_window="night",
        trigger="inicio_semestre",
        message_text="Hola María, tenemos una oferta...",
        message_source="template",
        batch_id=batch_id,
    )


class TestSqlPersonRepository:
    def test_unknown_person_returns_none(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        assert repo.get_person("99999999") is None

    def test_save_and_get_roundtrip(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        repo.save_person(_maria())

        person = repo.get_person("10000001")

        assert person is not None
        assert person["nombre"] == "María Gómez"
        assert person["edad"] == 32
        assert person["categoria_afiliacion"] == "A"
        assert person["mora_maxima_historica"] == "0_DIAS"

    def test_multilabels_roundtrip_as_lists(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        repo.save_person(_maria())

        person = repo.get_person("10000001")

        assert person["intereses"] == ["educacion"]
        assert person["momentos_clave"] == ["inicio_semestre"]
        assert isinstance(person["area_trabajo"], list)

    def test_numerics_come_back_as_floats(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        repo.save_person(_maria())

        person = repo.get_person("10000001")

        assert isinstance(person["ingresos"], float)
        assert person["ingresos"] == 2_600_000.0
        assert isinstance(person["capacidad_endeudamiento_disponible_pct"], float)

    def test_consents_come_back_as_bools(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        repo.save_person(_maria())

        person = repo.get_person("10000001")

        assert person["consent_whatsapp"] is True
        assert person["consent_email"] is False
        assert person["telefono"] == "573001112233"

    def test_save_person_upserts(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        repo.save_person(_maria())
        updated = _maria()
        updated["nombre"] = "María Gómez de Pérez"
        repo.save_person(updated)

        person = repo.get_person("10000001")

        assert person["nombre"] == "María Gómez de Pérez"

    def test_bulk_lookup(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        for persona in DEMO_PERSONS.values():
            repo.save_person(persona)

        found = repo.get_persons_by_ids(["10000001", "P0001", "99999999"])

        assert set(found) == {"10000001", "P0001"}
        assert found["P0001"]["nombre"] == "Paula Nieto"

    def test_bulk_lookup_empty_input(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        assert repo.get_persons_by_ids([]) == {}

    def test_null_multilabel_column_loads_as_empty_list(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        persona = _maria()
        persona["intereses"] = None
        repo.save_person(persona)

        person = repo.get_person("10000001")

        assert person["intereses"] == []

    def test_delete_all_persons_clears_scheduled_messages_first(self, session_factory):
        # The outbox FK references persons (no cascade): a dataset replace
        # must clear messages first or SQL Server rejects the delete.
        repo = SqlPersonRepository(session_factory)
        repo.save_person(_maria())
        outbox = SqlOutbox(session_factory)
        outbox.save(_message())

        removed = repo.delete_all_persons()

        assert removed == 1
        assert repo.get_person("10000001") is None
        assert outbox.for_person("10000001") == []


class TestSqlOutbox:
    def _seed_person(self, session_factory, person_id: str = "10000001"):
        repo = SqlPersonRepository(session_factory)
        persona = dict(DEMO_PERSONS[person_id])
        repo.save_person(persona)

    def test_save_and_read_roundtrip(self, session_factory):
        self._seed_person(session_factory)
        outbox = SqlOutbox(session_factory)
        outbox.save(_message())

        messages = outbox.for_person("10000001")

        assert len(messages) == 1
        stored = messages[0]
        assert stored.person_id == "10000001"
        assert stored.product_id == "educativo"
        assert stored.trigger == "inicio_semestre"  # trigger_event column mapped back
        assert stored.batch_id == "batch-A"
        assert stored.status == "scheduled"
        assert stored.message_source == "template"

    def test_for_batch_filters(self, session_factory):
        self._seed_person(session_factory)
        outbox = SqlOutbox(session_factory)
        outbox.save(_message(batch_id="batch-A"))
        outbox.save(_message(batch_id="batch-B"))

        assert len(outbox.for_batch("batch-A")) == 1
        assert len(outbox.for_batch("batch-B")) == 1
        assert outbox.for_batch("batch-C") == []

    def test_for_person_returns_insertion_order(self, session_factory):
        self._seed_person(session_factory)
        outbox = SqlOutbox(session_factory)
        first = _message(batch_id="batch-A")
        second = _message(batch_id="batch-B")
        outbox.save(first)
        outbox.save(second)

        messages = outbox.for_person("10000001")

        assert [m.batch_id for m in messages] == ["batch-A", "batch-B"]

    def test_empty_batch_id_stored_as_null_reads_back_empty(self, session_factory):
        self._seed_person(session_factory)
        outbox = SqlOutbox(session_factory)
        outbox.save(_message(batch_id=""))

        messages = outbox.for_person("10000001")

        assert messages[0].batch_id == ""

    def test_created_at_roundtrips_tz_aware_and_equal(self, session_factory):
        # Storage is naive UTC (SYSUTCDATETIME semantics); the contract
        # boundary re-attaches UTC so SqlOutbox behaves like InMemoryOutbox.
        self._seed_person(session_factory)
        outbox = SqlOutbox(session_factory)
        original = _message()
        outbox.save(original)

        stored = outbox.for_person("10000001")[0]

        assert stored.created_at.tzinfo is not None
        assert stored.created_at == original.created_at

    def test_batch_id_case_survives_roundtrip(self, session_factory):
        self._seed_person(session_factory)
        outbox = SqlOutbox(session_factory)
        lowercase_uuid = "0fe4a1b2-3c4d-5e6f-7a8b-9c0d1e2f3a4b"
        outbox.save(_message(batch_id=lowercase_uuid))

        stored = outbox.for_batch(lowercase_uuid)

        assert len(stored) == 1
        assert stored[0].batch_id == lowercase_uuid
