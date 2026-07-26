"""Data contracts at module boundaries."""

from credit_engine.ml.schemas.input import InputSchemaError, validate_input
from credit_engine.ml.schemas.output import PredictionOutput, ProductPrediction

__all__ = [
    "InputSchemaError",
    "PredictionOutput",
    "ProductPrediction",
    "validate_input",
]
