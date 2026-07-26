"""Feature allowlist and encoding vocabularies.

Defines the 31-feature contract (25 numerical + 6 categorical) that all 9
models consume. Anything outside this list is stripped at inference time.
"""

from __future__ import annotations

NUMERICAL_FEATURES: list[str] = [
    # Profile
    "age",
    "income",
    "tenure_months",
    "job_tenure_months",
    "dependents",
    "internal_score",
    "debt_ratio",
    # Behavior
    "subsidy_usage_12m",
    "supermarket_usage_12m",
    "recreation_usage_12m",
    "education_usage_12m",
    "services_usage_index",
    "months_since_last_credit",
    "current_delinquency",
    "active_credit",
    "has_mortgage",
    # Declared exogenous signals
    "digital_affinity",
    "months_since_event",
    "education_interest",
    "housing_interest",
    "consolidation_interest",
    "tax_interest",
    "tourism_interest",
    "tech_interest",
    "health_interest",
]

CATEGORICAL_FEATURES: list[str] = [
    "category",
    "contract_type",
    "company_size",
    "city",
    "life_event",
    "job_sector",
]

ALL_FEATURES: list[str] = [*NUMERICAL_FEATURES, *CATEGORICAL_FEATURES]

TARGET_PREFIX = "tomo_"
DEFAULT_TARGET = "default_12m"

PRODUCT_TARGETS: dict[str, str] = {
    "revolving_line": "tomo_cupo_rotativo",
    "personal_loan": "tomo_libre_inversion",
    "mortgage": "tomo_hipotecario",
    "education": "tomo_educativo",
    "debt_consolidation": "tomo_compra_cartera",
    "womens_credit": "tomo_mujer",
    "tax_insurance": "tomo_impuestos_seguros",
    "complementary_mortgage": "tomo_complementario_hipotecario",
}

ALL_TARGETS: list[str] = list(PRODUCT_TARGETS.values()) + [DEFAULT_TARGET]

OOV_THRESHOLD = 0.20
