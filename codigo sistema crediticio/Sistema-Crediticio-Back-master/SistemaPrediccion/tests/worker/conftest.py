import pytest

from credit_engine.worker.contracts import Offer


@pytest.fixture
def make_offer():
    """Factory fixture: build a valid Offer with overridable fields."""

    def _make(**overrides) -> Offer:
        fields = {
            "person_id": "P00123",
            "person_name": "María",
            "product_id": "educativo",
            "product_name": "Crédito Educativo",
            "amount_cop": "$5.600.000",
            "annual_rate_pct": "14,5% E.A.",
            "term_months": 36,
            "cuota_cop": "$192.000",
            "channel": "whatsapp",
            "contact_window": "night",
            "trigger": "inicio de semestre académico",
            "reason": "Te recomendamos el Crédito Educativo porque tienes 2 personas a cargo.",
        }
        fields.update(overrides)
        return Offer(**fields)

    return _make
