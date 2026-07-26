from credit_engine.llm import GenerationError, LLMClientError
from credit_engine.worker.composer import LLM_CHANNELS, DeliveryComposer


class RecordingGenerator:
    """Fake TextGenerator that records the call and returns fixed text."""

    def __init__(self, text: str = "Mensaje generado por LLM"):
        self.text = text
        self.calls: list[dict] = []

    def generate_message(self, person_name: str, product: str, benefits: str, channel: str) -> str:
        self.calls.append(
            {"person_name": person_name, "product": product, "benefits": benefits, "channel": channel}
        )
        return self.text


class FailingGenerator:
    def __init__(self, exc: Exception):
        self.exc = exc

    def generate_message(self, person_name: str, product: str, benefits: str, channel: str) -> str:
        raise self.exc


class TestLlmPath:
    def test_uses_llm_for_whatsapp(self, make_offer):
        generator = RecordingGenerator()
        composer = DeliveryComposer(generator)

        result = composer.compose(make_offer(channel="whatsapp"))

        assert result.source == "llm"
        assert result.text == "Mensaje generado por LLM"
        assert len(generator.calls) == 1

    def test_maps_offer_fields_to_generator_args(self, make_offer):
        generator = RecordingGenerator()
        composer = DeliveryComposer(generator)
        offer = make_offer()

        composer.compose(offer)

        call = generator.calls[0]
        assert call["person_name"] == offer.person_name
        assert call["product"] == offer.product_name
        assert call["channel"] == offer.channel

    def test_benefits_include_reason_and_financial_terms(self, make_offer):
        generator = RecordingGenerator()
        composer = DeliveryComposer(generator)
        offer = make_offer()

        composer.compose(offer)

        benefits = generator.calls[0]["benefits"]
        assert offer.reason in benefits
        assert offer.amount_cop in benefits
        assert offer.annual_rate_pct in benefits
        assert str(offer.term_months) in benefits
        assert offer.cuota_cop in benefits


class TestTemplateFallback:
    def test_falls_back_on_llm_client_error(self, make_offer):
        composer = DeliveryComposer(FailingGenerator(LLMClientError("boom")))
        offer = make_offer()

        result = composer.compose(offer)

        assert result.source == "template"
        assert offer.amount_cop in result.text
        assert offer.person_name in result.text

    def test_falls_back_on_generation_error(self, make_offer):
        composer = DeliveryComposer(FailingGenerator(GenerationError("empty")))

        result = composer.compose(make_offer())

        assert result.source == "template"

    def test_template_only_when_no_generator(self, make_offer):
        composer = DeliveryComposer(None)
        offer = make_offer()

        result = composer.compose(offer)

        assert result.source == "template"
        assert offer.product_name in result.text
        assert offer.cuota_cop in result.text

    def test_template_contains_reason(self, make_offer):
        composer = DeliveryComposer(None)
        offer = make_offer()

        result = composer.compose(offer)

        assert offer.reason in result.text

    def test_blank_person_name_uses_nameless_greeting(self, make_offer):
        composer = DeliveryComposer(FailingGenerator(GenerationError("person_name must not be empty")))

        result = composer.compose(make_offer(person_name=""))

        assert result.source == "template"
        assert result.text.startswith("Hola, tenemos")
        assert "Hola ," not in result.text


class TestNonLlmChannels:
    def test_app_channel_never_calls_generator(self, make_offer):
        generator = RecordingGenerator()
        composer = DeliveryComposer(generator)

        result = composer.compose(make_offer(channel="app"))

        assert result.source == "template"
        assert generator.calls == []

    def test_llm_channels_are_exactly_three(self):
        assert LLM_CHANNELS == ("whatsapp", "sms", "email")
