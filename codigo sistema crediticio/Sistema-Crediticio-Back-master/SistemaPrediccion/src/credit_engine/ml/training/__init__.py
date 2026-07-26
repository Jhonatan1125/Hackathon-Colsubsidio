"""Training sub-package — offline-only training lifecycle.

These scripts execute offline and produce serialized artifacts consumed at runtime.
Never imported in production inference path.
"""

from credit_engine.ml.training.baseline import train_woe_baseline, WoETransformer
from credit_engine.ml.training.calibrate import apply_calibration, compute_ece, fit_calibration
from credit_engine.ml.training.evaluate import (
    compute_fairness_audit,
    compute_gini,
    compute_ks,
    compute_lift_table,
    evaluate_model,
)
from credit_engine.ml.training.shap_explain import (
    compute_gain_importance,
    compute_global_shap_importance,
    compute_shap_values,
    get_local_shap_explanation,
    run_shap_analysis,
)
from credit_engine.ml.training.split import global_split, SplitResult
from credit_engine.ml.training.train import train_lightgbm

__all__ = [
    "SplitResult",
    "WoETransformer",
    "apply_calibration",
    "compute_ece",
    "compute_fairness_audit",
    "compute_gain_importance",
    "compute_gini",
    "compute_global_shap_importance",
    "compute_ks",
    "compute_lift_table",
    "compute_shap_values",
    "evaluate_model",
    "fit_calibration",
    "get_local_shap_explanation",
    "global_split",
    "run_shap_analysis",
    "train_lightgbm",
    "train_woe_baseline",
]
