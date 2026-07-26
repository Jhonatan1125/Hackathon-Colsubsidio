"""SHAP explainability — gain-based global importance and local SHAP decomposition.

Uses TreeExplainer for exact SHAP values on tree-based models.
Global: mean |SHAP| across sample. Local: top-3 positive contributions per prediction.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import shap

    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


def compute_gain_importance(model: object, feature_names: list[str]) -> pd.DataFrame:
    """Compute gain-based feature importance from LightGBM model.

    Args:
        model: Trained LightGBM classifier.
        feature_names: List of feature names.

    Returns:
        DataFrame with feature names and gain importance, sorted descending.
    """
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "booster_"):
        importances = model.booster_.feature_importance(importance_type="gain")
    else:
        logger.warning("Model does not expose feature importances.")
        return pd.DataFrame({"feature": feature_names, "gain": 0.0})

    importance_df = pd.DataFrame({
        "feature": feature_names,
        "gain": importances,
    }).sort_values("gain", ascending=False).reset_index(drop=True)

    return importance_df


def compute_shap_values(
    model: object,
    X: pd.DataFrame,
    sample_size: int | None = None,
) -> tuple[np.ndarray, dict]:
    """Compute SHAP values using TreeExplainer.

    Args:
        model: Trained tree-based model (LightGBM).
        X: Feature DataFrame for SHAP computation.
        sample_size: Number of rows to sample (None = all).

    Returns:
        Tuple of (shap_values array, explainer metadata).
    """
    if not HAS_SHAP:
        raise ImportError(
            "shap is required for SHAP explainability. "
            "Install with: pip install shap"
        )

    X_sample = X.sample(n=sample_size, random_state=42) if sample_size else X

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    metadata = {
        "base_value": float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.0,
        "sample_size": len(X_sample),
        "n_features": len(X.columns),
        "feature_names": list(X.columns),
    }

    return shap_values, metadata


def compute_global_shap_importance(
    shap_values: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Compute global SHAP importance (mean |SHAP| across sample).

    Args:
        shap_values: SHAP value array (n_samples, n_features).
        feature_names: List of feature names.

    Returns:
        DataFrame with mean absolute SHAP values, sorted descending.
    """
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    importance_df = pd.DataFrame({
        "feature": feature_names,
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

    return importance_df


def get_local_shap_explanation(
    shap_values: np.ndarray,
    feature_values: pd.DataFrame,
    feature_names: list[str],
    sample_idx: int = 0,
    top_k: int = 3,
) -> list[dict]:
    """Get top-k positive SHAP contributions for a single prediction.

    Args:
        shap_values: SHAP value array.
        feature_values: Original feature values DataFrame.
        feature_names: List of feature names.
        sample_idx: Index of the sample to explain.
        top_k: Number of top positive contributions to return.

    Returns:
        List of dicts with feature name, value, and SHAP contribution.
    """
    sample_shap = shap_values[sample_idx]
    sample_features = feature_values.iloc[sample_idx]

    positive_indices = np.where(sample_shap > 0)[0]
    if len(positive_indices) == 0:
        return []

    top_indices = positive_indices[np.argsort(sample_shap[positive_indices])[-top_k:][::-1]]

    explanations = []
    for idx in top_indices:
        explanations.append({
            "feature": feature_names[idx],
            "value": sample_features.iloc[idx],
            "shap_contribution": float(sample_shap[idx]),
        })

    return explanations


def run_shap_analysis(
    model: object,
    X: pd.DataFrame,
    model_name: str,
    sample_size: int = 1000,
    output_dir: Path | None = None,
) -> dict:
    """Run complete SHAP analysis: global importance + local explanations.

    Args:
        model: Trained tree-based model.
        X: Feature DataFrame.
        model_name: Name for the model.
        sample_size: Number of samples for SHAP computation.
        output_dir: Directory to save SHAP artifacts.

    Returns:
        Dictionary with global importance, sample local explanations, and metadata.
    """
    gain_importance = compute_gain_importance(model, list(X.columns))
    shap_values, shap_metadata = compute_shap_values(model, X, sample_size=sample_size)
    global_shap = compute_global_shap_importance(shap_values, list(X.columns))

    local_explanations = []
    n_samples = min(5, len(X))
    for i in range(n_samples):
        local_exp = get_local_shap_explanation(
            shap_values, X, list(X.columns), sample_idx=i, top_k=3
        )
        local_explanations.append({
            "sample_idx": i,
            "explanations": local_exp,
        })

    results = {
        "model_name": model_name,
        "gain_importance": gain_importance.to_dict(orient="records"),
        "global_shap_importance": global_shap.to_dict(orient="records"),
        "sample_local_explanations": local_explanations,
        "shap_metadata": shap_metadata,
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

        shap_path = output_dir / f"{model_name}_shap.joblib"
        joblib.dump({
            "shap_values": shap_values,
            "global_shap": global_shap,
            "gain_importance": gain_importance,
        }, shap_path)

        report_path = output_dir / f"{model_name}_shap_report.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=_json_serializer)

        logger.info("Saved SHAP analysis to %s", output_dir)

    return results


def _json_serializer(obj: object) -> str:
    """JSON serializer for numpy types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)
