"""ML Module — Models layer: training to inference lifecycle.

Public API exports:
- Predictor: Runtime inference engine (loads 9 serialized artifacts)
- Schema classes: Input/output data contracts

Training scripts are isolated in ml.training/ and never imported at runtime.
"""

from credit_engine.ml.predictor import Predictor
from credit_engine.ml.schemas.output import PredictionOutput, ProductPrediction

__all__ = [
    "PredictionOutput",
    "Predictor",
    "ProductPrediction",
]
