"""Isotonic calibration fitting on validation set raw scores.

Fits isotonic regression to map raw LightGBM scores to calibrated probabilities.
Non-decreasing transformation preserves rank order while improving probability scale.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss

logger = logging.getLogger(__name__)


def compute_ece(y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error.

    Args:
        y_true: Binary ground truth labels.
        y_pred: Predicted probabilities.
        n_bins: Number of bins for calibration assessment.

    Returns:
        ECE value (lower is better calibrated).
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n_samples = len(y_true)

    for i in range(n_bins):
        mask = (y_pred >= bin_boundaries[i]) & (y_pred < bin_boundaries[i + 1])
        if i == n_bins - 1:
            mask = (y_pred >= bin_boundaries[i]) & (y_pred <= bin_boundaries[i + 1])

        bin_size = mask.sum()
        if bin_size == 0:
            continue

        bin_accuracy = y_true[mask].mean()
        bin_confidence = y_pred[mask].mean()
        ece += (bin_size / n_samples) * abs(bin_accuracy - bin_confidence)

    return float(ece)


def fit_calibration(
    y_val: np.ndarray,
    raw_scores_val: np.ndarray,
    model_name: str,
    output_dir: Path | None = None,
) -> dict:
    """Fit isotonic regression calibrator on validation set.

    Args:
        y_val: Validation ground truth labels.
        raw_scores_val: Raw model scores on validation set.
        model_name: Name for the model.
        output_dir: Directory to save calibration artifact.

    Returns:
        Dictionary with calibrator, metrics, and calibration curves.
    """
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    calibrator.fit(raw_scores_val, y_val)

    calibrated_scores = calibrator.predict(raw_scores_val)

    raw_brier = float(brier_score_loss(y_val, raw_scores_val))
    calibrated_brier = float(brier_score_loss(y_val, calibrated_scores))

    raw_ece = compute_ece(y_val, raw_scores_val)
    calibrated_ece = compute_ece(y_val, calibrated_scores)

    metadata = {
        "model_name": model_name,
        "raw_brier_score": raw_brier,
        "calibrated_brier_score": calibrated_brier,
        "raw_ece": raw_ece,
        "calibrated_ece": calibrated_ece,
        "ece_improvement": raw_ece - calibrated_ece,
    }

    logger.info(
        "Calibration for %s: ECE %.4f -> %.4f (improvement: %.4f)",
        model_name,
        raw_ece,
        calibrated_ece,
        raw_ece - calibrated_ece,
    )

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = {
            "calibrator": calibrator,
            "metadata": metadata,
        }
        cal_path = output_dir / f"{model_name}_calibration.joblib"
        joblib.dump(artifact, cal_path)
        logger.info("Saved calibration curve to %s", cal_path)

        meta_path = output_dir / f"{model_name}_calibration_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

    return {
        "calibrator": calibrator,
        "metadata": metadata,
        "raw_ece": raw_ece,
        "calibrated_ece": calibrated_ece,
    }


def apply_calibration(
    calibrator: IsotonicRegression,
    raw_scores: np.ndarray,
) -> np.ndarray:
    """Apply fitted isotonic calibrator to raw scores.

    Args:
        calibrator: Fitted IsotonicRegression instance.
        raw_scores: Raw model scores to calibrate.

    Returns:
        Calibrated probabilities.
    """
    return calibrator.predict(raw_scores)
