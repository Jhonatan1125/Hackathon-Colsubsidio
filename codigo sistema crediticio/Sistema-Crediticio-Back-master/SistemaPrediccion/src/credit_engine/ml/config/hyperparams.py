"""LightGBM and WoE baseline hyperparameters.

All training parameters are centralized here. No magic numbers in logic modules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LightGBMConfig:
    """LightGBM hyperparameters tuned for low-prevalence regimes."""

    n_estimators: int = 2000
    learning_rate: float = 0.03
    num_leaves: int = 15
    min_child_samples: int = 100
    early_stopping_rounds: int = 100
    random_state: int = 42
    first_metric_only: bool = True


@dataclass(frozen=True)
class WoEBaselineConfig:
    """Weight of Evidence + Logistic Regression baseline configuration."""

    n_bins: int = 10
    min_bin_size: int = 50
    monotonic_trend: str = "auto"
    solver: str = "lbfgs"
    max_iter: int = 1000


@dataclass(frozen=True)
class ModelSelectionConfig:
    """Criteria for selecting between LightGBM and WoE baseline."""

    min_auc_margin: float = 0.005


LIGHTGBM = LightGBMConfig()
WOE_BASELINE = WoEBaselineConfig()
MODEL_SELECTION = ModelSelectionConfig()
