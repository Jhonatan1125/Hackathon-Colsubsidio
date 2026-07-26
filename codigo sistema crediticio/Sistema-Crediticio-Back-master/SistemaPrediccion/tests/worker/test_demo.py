from credit_engine.ingestion.validator import MIN_BATCH_SIZE, is_valid_person_id, sanitize_id
from credit_engine.worker.demo import DEMO_PERSONS, DemoOfferEngine, build_demo_repository


class TestDemoPersons:
    def test_has_at_least_min_batch_size_personas(self):
        assert len(DEMO_PERSONS) >= MIN_BATCH_SIZE

    def test_all_ids_pass_ingestion_validation(self):
        for person_id in DEMO_PERSONS:
            assert is_valid_person_id(sanitize_id(person_id)), person_id

    def test_personas_follow_dataset_schema(self):
        required = {
            "cedula",
            "nombre",
            "edad",
            "ingresos",
            "score_datacredito",
            "categoria_afiliacion",
            "mora_maxima_historica",
            "intereses",
            "momentos_clave",
            "capacidad_endeudamiento_disponible_pct",
        }
        for person in DEMO_PERSONS.values():
            assert required <= set(person.keys())

    def test_build_demo_repository_finds_personas(self):
        repo = build_demo_repository()
        assert repo.get_person("10000001") is not None
        assert repo.get_person("P0001") is not None
        assert repo.get_person("99999999") is None


class TestDemoOfferEngine:
    def setup_method(self):
        self.engine = DemoOfferEngine()
        self.repo = build_demo_repository()

    def test_education_interest_maps_to_educativo(self):
        offer = self.engine.evaluate(self.repo.get_person("10000001"))
        assert offer is not None
        assert offer.product_id == "educativo"

    def test_consolidation_interest_maps_to_compra_cartera(self):
        offer = self.engine.evaluate(self.repo.get_person("10000002"))
        assert offer is not None
        assert offer.product_id == "compra_cartera"

    def test_housing_interest_maps_to_hipotecario(self):
        offer = self.engine.evaluate(self.repo.get_person("10000003"))
        assert offer is not None
        assert offer.product_id == "hipotecario"

    def test_no_matching_interest_defaults_to_libre_inversion(self):
        offer = self.engine.evaluate(self.repo.get_person("10000004"))
        assert offer is not None
        assert offer.product_id == "libre_inversion"

    def test_tolerates_null_multilabel_fields(self):
        # A dbo.persons row may legally carry NULL multilabel columns —
        # the engine must not crash and defaults to libre_inversion.
        person = self.repo.get_person("10000004")
        person["intereses"] = None
        person["momentos_clave"] = None

        offer = self.engine.evaluate(person)

        assert offer is not None
        assert offer.product_id == "libre_inversion"
        assert offer.trigger == "inmediato"
        assert "tu perfil financiero" in offer.reason

    def test_high_delinquency_gets_no_offer(self):
        offer = self.engine.evaluate(self.repo.get_person("10000006"))
        assert offer is None

    def test_financial_terms_are_display_ready_cop(self):
        offer = self.engine.evaluate(self.repo.get_person("10000001"))
        assert offer.amount_cop.startswith("$")
        assert "." in offer.amount_cop  # thousands separator
        assert offer.cuota_cop.startswith("$")
        assert offer.annual_rate_pct.endswith("% E.A.")
        assert offer.term_months == 36

    def test_channel_respects_whatsapp_consent(self):
        offer = self.engine.evaluate(self.repo.get_person("10000001"))
        assert offer.channel == "whatsapp"

    def test_channel_falls_back_to_email_consent(self):
        offer = self.engine.evaluate(self.repo.get_person("10000002"))
        assert offer.channel == "email"

    def test_channel_falls_back_to_app_without_consents(self):
        offer = self.engine.evaluate(self.repo.get_person("P0003"))
        assert offer.channel == "app"

    def test_window_by_age(self):
        young = self.engine.evaluate(self.repo.get_person("10000001"))  # 32
        older = self.engine.evaluate(self.repo.get_person("10000002"))  # 45
        assert young.contact_window == "night"
        assert older.contact_window == "morning"

    def test_trigger_from_momentos_clave(self):
        offer = self.engine.evaluate(self.repo.get_person("10000001"))
        assert offer.trigger == "inicio_semestre"

    def test_trigger_defaults_to_inmediato(self):
        offer = self.engine.evaluate(self.repo.get_person("10000002"))
        assert offer.trigger == "inmediato"

    def test_offer_carries_person_identity(self):
        offer = self.engine.evaluate(self.repo.get_person("10000001"))
        assert offer.person_id == "10000001"
        assert offer.person_name == "María Gómez"
        assert offer.reason
