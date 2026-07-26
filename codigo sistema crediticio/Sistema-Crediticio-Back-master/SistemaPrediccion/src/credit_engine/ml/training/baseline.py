"""WoE (Weight of Evidence) + Logistic Regression baseline.

Classic banking scorecard approach: OptBinning for feature discretization
followed by Logistic Regression on WoE-transformed features.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from credit_engine.ml.config.hyperparams import WOE_BASELINE

logger = logging.getLogger(__name__)

try:
    from optbinning import OptBinning

    HAS_OPTBINNING = True
except ImportError:
    HAS_OPTBINNING = False


class WoETransformer:
    """Weight of Evidence transformation with OptBinning."""

    def __init__(self) -> None:
        self._binners: dict[str, object] = {}
        self._woe_tables: dict[str, dict] = {}

    def fit_transform(self, X: pd.DataFrame, y: pd.Series | np.ndarray) -> pd.DataFrame:
        """Fit OptBinning per feature and return WoE-transformed DataFrame."""
        if not HAS_OPTBINNING:
            raise ImportError(
                "optbinning is required for WoE baseline. "
                "Install with: pip install optbinning"
            )

        X_woe = pd.DataFrame(index=X.index)

        for col in X.columns:
            try:
                binner = OptBinning(
                    name=col,
                    dtype="numerical" if col in X.select_dtypes(include="number").columns else "categorical",
                    min_n_bins=WOE_BASELINE.n_bins,
                    min_bin_size=WOE_BASELINE.min_bin_size,
                    monotonic_trend=WOE_BASELINE.monotonic_trend,
                    verbose=False,
                )
                binner.fit(X[col].values, y)
                X_woe[col] = binner.transform(X[col].values)
                self._binners[col] = binner
                self._woe_tables[col] = binner.binning_table.build().to_dict()
            except Exception as e:
                logger.warning("WoE binning failed for '%s': %s. Using raw values.", col, e)
                X_woe[col] = X[col].values

        return X_woe

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply fitted WoE transformation."""
        X_woe = pd.DataFrame(index=X.index)
        for col in X.columns:
            if col in self._binners:
                try:
                    X_woe[col] = self._binners[col].transform(X[col].values)
                except Exception:
                    X_woe[col] = X[col].values
            else:
                X_woe[col] = X[col].values
        return X_woe

    def get_scorecard(self) -> dict:
        """Return WoE tables for auditing."""
        return self._woe_tables


def train_woe_baseline(
    X_train: pd.DataFrame,
    y_train: pd.Series | np.ndarray,
    X_val: pd.DataFrame,
    y_val: pd.Series | np.ndarray,
    model_name: str,
    output_dir: Path | None = None,
) -> dict:
    """Train WoE + Logistic Regression baseline.

    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        model_name: Name for the model.
        output_dir: Directory to save artifacts.

    Returns:
        Dictionary with pipeline, metadata, and validation AUC.
    """
    if not HAS_OPTBINNING:
        logger.warning("optbinning not available. WoE baseline skipped.")
        return {"model": None, "metadata": None, "val_auc": 0.0}

    woer = WoETransformer()
    X_train_woe = woer.fit_transform(X_train, y_train)
    X_val_woe = woer.transform(X_val)

    lr = LogisticRegression(
        solver=WOE_BASELINE.solver,
        max_iter=WOE_BASELINE.max_iter,
        random_state=42,
    )
    lr.fit(X_train_woe, y_train)

    val_pred = lr.predict_proba(X_val_woe)[:, 1]
    val_auc = float(roc_auc_score(y_val, val_pred))

    metadata = {
        "model_name": model_name,
        "validation_auc": val_auc,
        "algorithm": "woe_logistic_regression",
        "coefficients": {
            col: float(coef) for col, coef in zip(X_train_woe.columns, lr.coef_[0])
        },
        "intercept": float(lr.intercept_[0]),
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = {
            "woe_transformer": woer,
            "logistic_regression": lr,
            "metadata": metadata,
        }
        model_path = output_dir / f"{model_name}_woe_lr.joblib"
        joblib.dump(artifact, model_path)
        logger.info("Saved WoE+LR baseline to %s", model_path)

        meta_path = output_dir / f"{model_name}_woe_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    return {
        "model": lr,
        "woe_transformer": woer,
        "metadata": metadata,
        "val_auc": val_auc,
    }
