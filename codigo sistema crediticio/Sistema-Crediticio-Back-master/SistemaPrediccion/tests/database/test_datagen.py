import json

from credit_engine.database.datagen import generate_personas
from credit_engine.database.repositories import SqlPersonRepository
from credit_engine.ingestion.validator import is_valid_person_id, sanitize_id
from credit_engine.worker.demo import DemoOfferEngine

_SAMPLE = 500


class TestGeneratePersonas:
    def test_generates_requested_count(self):
        assert len(generate_personas(_SAMPLE)) == _SAMPLE

    def test_deterministic_for_same_seed(self):
        assert generate_personas(200, seed=42) == generate_personas(200, seed=42)

    def test_different_seeds_differ(self):
        assert generate_personas(200, seed=42) != generate_personas(200, seed=7)

    def test_cedulas_are_unique_and_valid(self):
        personas = generate_personas(_SAMPLE)
        cedulas = [p["cedula"] for p in personas]
        assert len(set(cedulas)) == _SAMPLE
        assert all(is_valid_person_id(sanitize_id(c)) for c in cedulas)

    def test_rows_satisfy_ddl_check_constraints(self):
        for p in generate_personas(_SAMPLE):
            assert p["categoria_afiliacion"] in {"A", "B", "C", "D"}
            assert p["mora_maxima_historica"] in {"0_DIAS", "30_DIAS", "60_DIAS", "90_MAS_DIAS"}
            for field in (
                "area_trabajo",
                "intereses",
                "preferencias",
                "momentos_clave",
                "composicion_familiar",
                "historial_creditos",
            ):
                # JSON arrays — must pass the DDL's ISJSON checks once dumped
                assert isinstance(json.loads(json.dumps(p[field])), list)

    def test_income_matches_category_tiers(self):
        smmlv = 1_423_500
        for p in generate_personas(_SAMPLE):
            in_smmlv = p["ingresos"] / smmlv
            if p["categoria_afiliacion"] == "A":
                assert in_smmlv <= 2.05
            elif p["categoria_afiliacion"] == "B":
                assert 1.95 <= in_smmlv <= 4.05
            else:
                assert in_smmlv >= 3.95

    def test_score_within_bounds(self):
        for p in generate_personas(_SAMPLE):
            assert 150 <= p["score_datacredito"] <= 950
            assert 18 <= p["edad"] <= 69
            assert 5.0 <= p["capacidad_endeudamiento_disponible_pct"] <= 95.0

    def test_consent_implies_contact_data(self):
        for p in generate_personas(_SAMPLE):
            if p["consent_whatsapp"]:
                assert p["telefono"]
            if p["consent_email"]:
                assert p["correo"]

    def test_targets_come_from_catalog(self):
        catalog = {
            "educativo",
            "compra_cartera",
            "hipotecario",
            "impuestos_seguros",
            "libre_inversion",
            "cupo_rotativo",
        }
        personas = generate_personas(_SAMPLE)
        targets = {p["producto_colsubsidio_target"] for p in personas}
        assert targets - {None} <= catalog
        assert None in targets  # some rows have no product

    def test_interest_signal_reaches_target(self):
        # Planted signal: educacion-interested personas should skew educativo
        personas = generate_personas(2_000)
        con_educacion = [p for p in personas if "educacion" in p["intereses"]]
        rate = sum(1 for p in con_educacion if p["producto_colsubsidio_target"] == "educativo") / len(con_educacion)
        assert rate > 0.4  # dominant vs base rate

    def test_demo_engine_consumes_generated_personas(self):
        engine = DemoOfferEngine()
        offers = [engine.evaluate(p) for p in generate_personas(200)]
        assert any(o is not None for o in offers)  # engine works on generated data


class TestBulkLoad:
    def test_bulk_load_and_read_back(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        personas = generate_personas(_SAMPLE)

        inserted = repo.save_persons(personas, chunk_size=200)

        assert inserted == _SAMPLE
        first = repo.get_person(personas[0]["cedula"])
        assert first is not None
        assert first["nombre"] == personas[0]["nombre"]
        assert isinstance(first["intereses"], list)

    def test_delete_all_persons(self, session_factory):
        repo = SqlPersonRepository(session_factory)
        repo.save_persons(generate_personas(50))

        removed = repo.delete_all_persons()

        assert removed == 50
        assert repo.get_person("100000000") is None
