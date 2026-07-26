"""Product catalog with margins, rates, terms, and eligibility rules.

Each product declares its business parameters as configuration data.
Adding or modifying a product is a configuration change, not a code change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProductConfig:
    """Declarative product definition."""

    product_id: str
    target_column: str
    margin: float
    annual_rates: dict[str, float]
    term_months: int = 36
    min_amount_smmlv: float = 1.0
    max_amount_smmlv: float = 150.0
    allowed_categories: list[str] = field(default_factory=lambda: ["A", "B", "C"])
    min_age: int = 18
    max_age: int = 69
    min_internal_score: float = 0.0
    requires_no_delinquency: bool = False
    gender_restriction: str | None = None
    prerequisite_product: str | None = None


PRODUCTS: dict[str, ProductConfig] = {
    "revolving_line": ProductConfig(
        product_id="revolving_line",
        target_column="tomo_cupo_rotativo",
        margin=0.12,
        annual_rates={"A": 0.14, "B": 0.16, "C": 0.18},
        term_months=36,
        min_amount_smmlv=1.0,
        max_amount_smmlv=10.0,
    ),
    "personal_loan": ProductConfig(
        product_id="personal_loan",
        target_column="tomo_libre_inversion",
        margin=0.10,
        annual_rates={"A": 0.13, "B": 0.15, "C": 0.17},
        term_months=36,
        min_amount_smmlv=1.0,
        max_amount_smmlv=150.0,
    ),
    "mortgage": ProductConfig(
        product_id="mortgage",
        target_column="tomo_hipotecario",
        margin=0.05,
        annual_rates={"A": 0.09, "B": 0.10, "C": 0.11},
        term_months=180,
        min_amount_smmlv=50.0,
        max_amount_smmlv=500.0,
        allowed_categories=["A", "B"],
        max_age=65,
    ),
    "education": ProductConfig(
        product_id="education",
        target_column="tomo_educativo",
        margin=0.06,
        annual_rates={"A": 0.10, "B": 0.12, "C": 0.14},
        term_months=36,
        min_amount_smmlv=1.0,
        max_amount_smmlv=50.0,
    ),
    "debt_consolidation": ProductConfig(
        product_id="debt_consolidation",
        target_column="tomo_compra_cartera",
        margin=0.07,
        annual_rates={"A": 0.11, "B": 0.13, "C": 0.15},
        term_months=36,
        min_amount_smmlv=1.0,
        max_amount_smmlv=100.0,
    ),
    "womens_credit": ProductConfig(
        product_id="womens_credit",
        target_column="tomo_mujer",
        margin=0.09,
        annual_rates={"A": 0.12, "B": 0.14, "C": 0.16},
        term_months=36,
        min_amount_smmlv=1.0,
        max_amount_smmlv=15.0,
        gender_restriction="Female",
    ),
    "tax_insurance": ProductConfig(
        product_id="tax_insurance",
        target_column="tomo_impuestos_seguros",
        margin=0.11,
        annual_rates={"A": 0.13, "B": 0.15, "C": 0.17},
        term_months=11,
        min_amount_smmlv=0.5,
        max_amount_smmlv=10.0,
    ),
    "complementary_mortgage": ProductConfig(
        product_id="complementary_mortgage",
        target_column="tomo_complementario_hipotecario",
        margin=0.05,
        annual_rates={"A": 0.09, "B": 0.10, "C": 0.11},
        term_months=36,
        min_amount_smmlv=5.0,
        max_amount_smmlv=100.0,
        prerequisite_product="mortgage",
    ),
}
