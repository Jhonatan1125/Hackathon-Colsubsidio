"""Output schema for prediction payloads.

Defines the structured prediction payload returned to the Decision layer:
per-product raw score and calibrated probability.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProductPrediction:
    """Prediction for a single product."""

    product_id: str
    raw_score: float
    calibrated_probability: float


@dataclass(frozen=True)
class PredictionOutput:
    """Complete prediction payload for one member.

    Contains raw scores (for ranking/fairness) and calibrated probabilities
    (for expected value calculations) for all 8 propensity models plus
    the default risk model.
    """

    member_id: str
    propensity_predictions: dict[str, ProductPrediction] = field(default_factory=dict)
    default_prediction: ProductPrediction | None = None

    def get_calibrated_probability(self, product_id: str) -> float | None:
        """Get calibrated probability for a specific product."""
        pred = self.propensity_predictions.get(product_id)
        return pred.calibrated_probability if pred else None

    def get_raw_score(self, product_id: str) -> float | None:
        """Get raw score for a specific product."""
        pred = self.propensity_predictions.get(product_id)
        return pred.raw_score if pred else None

    @property
    def default_pd(self) -> float | None:
        """Get calibrated probability of default."""
        return self.default_prediction.calibrated_probability if self.default_prediction else None

    @property
    def default_raw_score(self) -> float | None:
        """Get raw default risk score."""
        return self.default_prediction.raw_score if self.default_prediction else None
