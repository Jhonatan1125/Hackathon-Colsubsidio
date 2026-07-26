"""Runtime inference — loads all 9 serialized artifacts.

Exposes predict_proba_raw (for ranking/fairness) and predict_proba (for EV calculations).
This is the sole runtime entry point from the Decision layer.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from credit_engine.ml.config.features import (
    ALL_FEATURES,
    ALL_TARGETS,
    CATEGORICAL_FEATURES,
    DEFAULT_TARGET,
    PRODUCT_TARGETS,
)
from credit_engine.ml.features import FeatureEngineer
from credit_engine.ml.schemas.output import PredictionOutput, ProductPrediction

logger = logging.getLogger(__name__)


class Predictor:
    """Loads and serves predictions from all 9 trained model artifacts.

    At worker startup, loads all serialized models and calibration curves
    into memory. Exposes two strictly separated prediction interfaces:
    - predict_proba_raw: raw LightGBM scores (for ranking, AUC, fairness)
    - predict_proba: isotonic-calibrated probabilities (for EV calculations)
    """

    def __init__(self, models_dir: Path | str | None = None) -> None:
        self._models_dir = Path(models_dir) if models_dir else Path(__file__).parent / "models"
        self._propensity_models: dict[str, object] = {}
        self._default_model: object | None = None
        self._calibrators: dict[str, IsotonicRegression] = {}
        self._default_calibrator: IsotonicRegression | None = None
        self._categorical_vocab: dict[str, set[str]] = {}
        self._loaded = False

    def load(self) -> Predictor:
        """Load all model artifacts from the models directory.

        Returns:
            Self with all models loaded.

        Raises:
            FileNotFoundError: If model artifacts are missing.
        """
        logger.info("Loading ML models from: %s", self._models_dir)
        if not self._models_dir.exists():
            logger.error("Models directory not found: %s", self._models_dir)
            raise FileNotFoundError(f"Models directory not found: {self._models_dir}")

        loaded_count = 0
        for product_id, target_col in PRODUCT_TARGETS.items():
            model_path = self._models_dir / f"{target_col}_lightgbm.joblib"
            if model_path.exists():
                artifact = joblib.load(model_path)
                self._propensity_models[product_id] = artifact["model"]
                loaded_count += 1
                logger.info("Loaded propensity model: %s (target: %s)", product_id, target_col)

                cal_path = self._models_dir / f"{target_col}_calibration.joblib"
                if cal_path.exists():
                    cal_artifact = joblib.load(cal_path)
                    self._calibrators[product_id] = cal_artifact["calibrator"]
                    logger.debug("Loaded calibration for: %s", product_id)
                else:
                    logger.debug("No calibration found for: %s", product_id)

                meta_path = self._models_dir / f"{target_col}_metadata.json"
                if meta_path.exists():
                    with open(meta_path) as f:
                        metadata = json.load(f)
                    if "categorical_features" in metadata:
                        for feat in metadata["categorical_features"]:
                            if feat not in self._categorical_vocab:
                                self._categorical_vocab[feat] = set()
            else:
                logger.debug("Model not found for product %s (expected: %s)", product_id, model_path)

        default_path = self._models_dir / f"{DEFAULT_TARGET}_lightgbm.joblib"
        if default_path.exists():
            artifact = joblib.load(default_path)
            self._default_model = artifact["model"]
            loaded_count += 1
            logger.info("Loaded default risk model: %s", DEFAULT_TARGET)

            cal_path = self._models_dir / f"{DEFAULT_TARGET}_calibration.joblib"
            if cal_path.exists():
                cal_artifact = joblib.load(cal_path)
                self._default_calibrator = cal_artifact["calibrator"]
                logger.debug("Loaded default calibration for: %s", DEFAULT_TARGET)
        else:
            logger.warning("Default risk model not found at: %s", default_path)

        vocab_path = self._models_dir / "categorical_vocab.json"
        if vocab_path.exists():
            with open(vocab_path) as f:
                raw_vocab = json.load(f)
            self._categorical_vocab = {k: set(v) for k, v in raw_vocab.items()}
            logger.debug("Loaded categorical vocab: %d features", len(self._categorical_vocab))

        self._loaded = True
        logger.info("ML model loading complete — %d models loaded, %d calibrators", loaded_count, len(self._calibrators))
        return self

    def predict_proba_raw(self, profiles: pd.DataFrame) -> dict[str, np.ndarray]:
        """Get raw LightGBM scores for ranking and fairness metrics.

        Args:
            profiles: DataFrame with raw member profiles.

        Returns:
            Dictionary mapping product_id to raw score arrays.
        """
        start = time.time()
        if not self._loaded:
            self.load()

        X = self._prepare_features(profiles)
        logger.debug("ML predict_proba_raw: %d profiles, %d features", len(profiles), X.shape[1])

        scores: dict[str, np.ndarray] = {}

        for product_id, model in self._propensity_models.items():
            raw_scores = model.predict_proba(X)[:, 1]
            scores[product_id] = raw_scores
            logger.debug("ML raw scores for %s: min=%.4f, max=%.4f, mean=%.4f", product_id, raw_scores.min(), raw_scores.max(), raw_scores.mean())

        if self._default_model is not None:
            scores["default_risk"] = self._default_model.predict_proba(X)[:, 1]
            logger.debug("ML default risk: min=%.4f, max=%.4f, mean=%.4f", scores["default_risk"].min(), scores["default_risk"].max(), scores["default_risk"].mean())

        logger.debug("ML predict_proba_raw completed in %.3fs — %d product(s)", time.time() - start, len(scores))
        return scores

    def predict_proba(self, profiles: pd.DataFrame) -> list[PredictionOutput]:
        """Get calibrated probabilities for expected value calculations.

        Args:
            profiles: DataFrame with raw member profiles.

        Returns:
            List of PredictionOutput, one per member.
        """
        start = time.time()
        if not self._loaded:
            self.load()

        logger.debug("ML predict_proba: %d profiles", len(profiles))
        raw_scores = self.predict_proba_raw(profiles)
        n_members = len(profiles)

        calibrated_scores: dict[str, np.ndarray] = {}
        for product_id in PRODUCT_TARGETS:
            if product_id in raw_scores:
                calibrated_scores[product_id] = self._calibrate_batch(
                    product_id, raw_scores[product_id]
                )
                logger.debug("ML calibrated %s: min=%.4f, max=%.4f", product_id, calibrated_scores[product_id].min(), calibrated_scores[product_id].max())

        default_calibrated = None
        if "default_risk" in raw_scores:
            default_calibrated = self._calibrate_default_batch(raw_scores["default_risk"])
            logger.debug("ML default calibrated: min=%.4f, max=%.4f", default_calibrated.min(), default_calibrated.max())

        outputs = []
        for i in range(n_members):
            member_id = str(profiles.index[i]) if profiles.index.name else str(i)

            propensity_preds = {}
            for product_id in PRODUCT_TARGETS:
                raw = raw_scores.get(product_id, np.array([0.0]))[i]
                calibrated = calibrated_scores.get(product_id, np.array([0.0]))[i]
                propensity_preds[product_id] = ProductPrediction(
                    product_id=product_id,
                    raw_score=float(raw),
                    calibrated_probability=float(calibrated),
                )

            default_pred = None
            if default_calibrated is not None:
                default_pred = ProductPrediction(
                    product_id="default_risk",
                    raw_score=float(raw_scores["default_risk"][i]),
                    calibrated_probability=float(default_calibrated[i]),
                )

            outputs.append(PredictionOutput(
                member_id=member_id,
                propensity_predictions=propensity_preds,
                default_prediction=default_pred,
            ))

        elapsed = time.time() - start
        logger.info("ML predict_proba completed in %.3fs — %d profiles, %d products", elapsed, n_members, len(PRODUCT_TARGETS))
        return outputs

    def predict_single(self, profile: dict[str, object]) -> PredictionOutput:
        """Get predictions for a single member profile.

        Args:
            profile: Dictionary with raw member features.

        Returns:
            PredictionOutput for the member.
        """
        return self.predict_proba(pd.DataFrame([profile]))[0]

    def _prepare_features(self, profiles: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for model input, enforcing allowlist."""
        available_features = [f for f in ALL_FEATURES if f in profiles.columns]
        X = profiles[available_features].copy()

        for col in CATEGORICAL_FEATURES:
            if col in X.columns:
                X[col] = X[col].astype("category")

        return X

    def _calibrate(self, product_id: str, raw_score: float) -> float:
        """Apply calibration to a raw propensity score."""
        calibrator = self._calibrators.get(product_id)
        if calibrator is None:
            return raw_score
        return float(calibrator.predict([raw_score])[0])

    def _calibrate_batch(self, product_id: str, raw_scores: np.ndarray) -> np.ndarray:
        """Apply calibration to a batch of raw propensity scores."""
        calibrator = self._calibrators.get(product_id)
        if calibrator is None:
            return raw_scores
        return calibrator.predict(raw_scores)

    def _calibrate_default(self, raw_score: float) -> float:
        """Apply calibration to a raw default risk score."""
        if self._default_calibrator is None:
            return raw_score
        return float(self._default_calibrator.predict([raw_score])[0])

    def _calibrate_default_batch(self, raw_scores: np.ndarray) -> np.ndarray:
        """Apply calibration to a batch of raw default risk scores."""
        if self._default_calibrator is None:
            return raw_scores
        return self._default_calibrator.predict(raw_scores)

    @property
    def is_loaded(self) -> bool:
        """Whether all model artifacts have been loaded."""
        return self._loaded

    @property
    def available_products(self) -> list[str]:
        """List of product IDs with loaded models."""
        return list(self._propensity_models.keys())
