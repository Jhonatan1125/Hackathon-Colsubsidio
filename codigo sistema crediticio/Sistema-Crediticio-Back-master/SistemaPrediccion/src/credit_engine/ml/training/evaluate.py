"""Evaluation metrics: AUC, KS, Gini, lift, Brier, ECE, ceiling comparison, fairness.

Computes final unseen test-set metrics and generates evaluation reports.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

logger = logging.getLogger(__name__)


def compute_ks(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Kolmogorov-Smirnov statistic using vectorized operations.

    Args:
        y_true: Binary ground truth labels.
        y_pred: Predicted probabilities or raw scores.

    Returns:
        KS statistic (maximum separation between TPR and FPR curves).
    """
    sorted_indices = np.argsort(y_pred)
    y_true_sorted = y_true[sorted_indices]
    y_pred_sorted = y_pred[sorted_indices]

    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)

    if n_pos == 0 or n_neg == 0:
        return 0.0

    tpr = np.cumsum(y_true_sorted) / n_pos
    fpr = np.cumsum(1 - y_true_sorted) / n_neg

    ks = float(np.max(np.abs(tpr - fpr)))
    return ks


def compute_gini(auc: float) -> float:
    """Compute Gini coefficient from AUC.

    Args:
        auc: Area under ROC curve.

    Returns:
        Gini coefficient = 2 * AUC - 1.
    """
    return 2.0 * auc - 1.0


def compute_lift_table(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_deciles: int = 10,
) -> pd.DataFrame:
    """Compute decile lift table.

    Args:
        y_true: Binary ground truth labels.
        y_pred: Predicted probabilities or raw scores.
        n_deciles: Number of deciles (default 10).

    Returns:
        DataFrame with lift metrics per decile.
    """
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred})
    df["decile"] = pd.qcut(df["y_pred"], q=n_deciles, labels=False, duplicates="drop")

    overall_rate = y_true.mean()

    lift_rows = []
    for decile in sorted(df["decile"].unique()):
        decile_mask = df["decile"] == decile
        decile_size = decile_mask.sum()
        decile_rate = df.loc[decile_mask, "y_true"].mean()
        lift = decile_rate / overall_rate if overall_rate > 0 else 0.0

        lift_rows.append({
            "decile": int(decile),
            "count": int(decile_size),
            "positive_rate": float(decile_rate),
            "lift": float(lift),
        })

    return pd.DataFrame(lift_rows)


def compute_fairness_audit(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    demographic_groups: dict[str, np.ndarray],
    top_k_pct: float = 0.20,
) -> dict:
    """Fairness audit using 4/5ths rule on top-k% ranked population.

    Args:
        y_true: Binary ground truth labels.
        y_pred: Predicted probabilities or raw scores.
        demographic_groups: Mapping of group names to boolean masks.
        top_k_pct: Fraction of top-ranked population to audit.

    Returns:
        Dictionary with fairness metrics per demographic group.
    """
    n_top = int(len(y_pred) * top_k_pct)
    top_indices = np.argsort(y_pred)[-n_top:]

    overall_top_rate = y_true[top_indices].mean() if n_top > 0 else 0.0

    audit_results = {}
    for group_name, group_mask in demographic_groups.items():
        group_top = np.intersect1d(top_indices, np.where(group_mask)[0])
        group_top_rate = y_true[group_top].mean() if len(group_top) > 0 else 0.0

        disparate_impact = group_top_rate / overall_top_rate if overall_top_rate > 0 else 1.0
        passes_four_fifths = disparate_impact >= 0.80

        audit_results[group_name] = {
            "group_selection_rate": float(group_top_rate),
            "overall_selection_rate": float(overall_top_rate),
            "disparate_impact_ratio": float(disparate_impact),
            "passes_four_fifths_rule": bool(passes_four_fifths),
        }

    return audit_results


def evaluate_model(
    y_test: np.ndarray,
    raw_scores: np.ndarray,
    calibrated_scores: np.ndarray | None = None,
    model_name: str = "unknown",
    synthetic_ceiling: float | None = None,
    demographic_groups: dict[str, np.ndarray] | None = None,
    output_dir: Path | None = None,
) -> dict:
    """Comprehensive model evaluation on unseen test set.

    Args:
        y_test: Test ground truth labels.
        raw_scores: Raw model scores on test set.
        calibrated_scores: Calibrated probabilities (optional).
        model_name: Name for the model.
        synthetic_ceiling: Theoretical maximum AUC for signal recovery check.
        demographic_groups: Demographic masks for fairness audit.
        output_dir: Directory to save evaluation report.

    Returns:
        Dictionary with all evaluation metrics.
    """
    auc = float(roc_auc_score(y_test, raw_scores))
    ks = compute_ks(y_test, raw_scores)
    gini = compute_gini(auc)
    brier = float(brier_score_loss(y_test, raw_scores))

    lift_table = compute_lift_table(y_test, raw_scores)

    metrics = {
        "model_name": model_name,
        "test_auc": auc,
        "test_ks": ks,
        "test_gini": gini,
        "brier_score": brier,
        "prevalence": float(y_test.mean()),
        "lift_table": lift_table.to_dict(orient="records"),
    }

    if calibrated_scores is not None:
        calibrated_ece = _compute_ece_simple(y_test, calibrated_scores)
        raw_ece = _compute_ece_simple(y_test, raw_scores)
        metrics["raw_ece"] = raw_ece
        metrics["calibrated_ece"] = calibrated_ece
        metrics["calibrated_brier"] = float(brier_score_loss(y_test, calibrated_scores))

    if synthetic_ceiling is not None:
        recovery_pct = auc / synthetic_ceiling if synthetic_ceiling > 0 else 0.0
        metrics["synthetic_ceiling"] = synthetic_ceiling
        metrics["signal_recovery_pct"] = recovery_pct

    if demographic_groups is not None:
        fairness = compute_fairness_audit(y_test, raw_scores, demographic_groups)
        metrics["fairness_audit"] = fairness

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"{model_name}_evaluation.json"
        with open(report_path, "w") as f:
            json.dump(metrics, f, indent=2, default=_json_serializer)
        logger.info("Saved evaluation report to %s", report_path)

    return metrics


def _compute_ece_simple(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> float:
    """Simple ECE computation."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n_samples = len(y_true)

    for i in range(n_bins):
        if i == n_bins - 1:
            mask = (y_pred >= bin_boundaries[i]) & (y_pred <= bin_boundaries[i + 1])
        else:
            mask = (y_pred >= bin_boundaries[i]) & (y_pred < bin_boundaries[i + 1])

        bin_size = mask.sum()
        if bin_size == 0:
            continue

        bin_accuracy = y_true[mask].mean()
        bin_confidence = y_pred[mask].mean()
        ece += (bin_size / n_samples) * abs(bin_accuracy - bin_confidence)

    return float(ece)


def _json_serializer(obj: object) -> str:
    """JSON serializer for numpy types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)
