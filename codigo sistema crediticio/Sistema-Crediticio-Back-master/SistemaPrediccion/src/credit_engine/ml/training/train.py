"""LightGBM training orchestration — one binary classifier per product.

Trains regularized LightGBM models with early stopping on validation AUC.
Produces serialized .joblib model files and training metadata.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from credit_engine.ml.config.features import CATEGORICAL_FEATURES, NUMERICAL_FEATURES
from credit_engine.ml.config.hyperparams import LIGHTGBM

logger = logging.getLogger(__name__)


def train_lightgbm(
    X_train: pd.DataFrame,
    y_train: pd.Series | np.ndarray,
    X_val: pd.DataFrame,
    y_val: pd.Series | np.ndarray,
    model_name: str,
    output_dir: Path | None = None,
) -> dict:
    """Train a LightGBM binary classifier with early stopping.

    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        model_name: Name for the model (used for artifact naming).
        output_dir: Directory to save artifacts. If None, artifacts are not saved.

    Returns:
        Dictionary with trained model, metadata, and validation metrics.
    """
    categorical_features = [c for c in CATEGORICAL_FEATURES if c in X_train.columns]

    train_data = lgb.Dataset(
        X_train,
        label=y_train,
        free_raw_data=False,
    )

    val_data = lgb.Dataset(
        X_val,
        label=y_val,
        reference=train_data,
        free_raw_data=False,
    )

    params = {
        "objective": "binary",
        "metric": "auc",
        "learning_rate": LIGHTGBM.learning_rate,
        "num_leaves": LIGHTGBM.num_leaves,
        "min_child_samples": LIGHTGBM.min_child_samples,
        "n_estimators": LIGHTGBM.n_estimators,
        "random_state": LIGHTGBM.random_state,
        "verbose": -1,
    }

    model = lgb.LGBMClassifier(**params)

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="auc",
        callbacks=[
            lgb.early_stopping(LIGHTGBM.early_stopping_rounds, first_metric_only=True),
            lgb.log_evaluation(period=0),
        ],
        categorical_feature=categorical_features if categorical_features else None,
    )

    best_iteration = model.best_iteration_ if hasattr(model, "best_iteration_") else model.n_estimators

    val_pred_raw = model.predict_proba(X_val)[:, 1]
    val_auc = float(lgb.roc_auc_score(y_val, val_pred_raw))

    metadata = {
        "model_name": model_name,
        "best_iteration": best_iteration,
        "n_estimators": LIGHTGBM.n_estimators,
        "learning_rate": LIGHTGBM.learning_rate,
        "num_leaves": LIGHTGBM.num_leaves,
        "min_child_samples": LIGHTGBM.min_child_samples,
        "validation_auc": val_auc,
        "feature_names": list(X_train.columns),
        "categorical_features": categorical_features,
        "algorithm": "lightgbm",
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / f"{model_name}_lightgbm.joblib"
        joblib.dump({"model": model, "metadata": metadata}, model_path)
        logger.info("Saved LightGBM model to %s", model_path)

        meta_path = output_dir / f"{model_name}_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

    return {
        "model": model,
        "metadata": metadata,
        "val_auc": val_auc,
    }
