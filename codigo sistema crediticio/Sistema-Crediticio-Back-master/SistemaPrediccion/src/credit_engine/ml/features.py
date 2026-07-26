"""Feature engineering — raw profile dict to model-ready vector.

Transforms raw person records from the Data layer into the 31-feature
vector consumed by predictor.py. Validates the allowlist contract and
handles categorical encoding using vocabularies stored during training.
"""

from __future__ import annotations

import warnings

import pandas as pd

from credit_engine.ml.config.features import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
)
from credit_engine.ml.schemas.input import InputSchemaError, validate_input


class FeatureEngineer:
    """Transforms raw member profiles into model-ready feature vectors.

    The allowlist contract is enforced here before features reach the predictor.
    Categorical encoding uses vocabularies persisted during training.
    """

    __slots__ = ("_categorical_vocab", "_fitted")

    def __init__(self, categorical_vocab: dict[str, set[str]] | None = None) -> None:
        self._categorical_vocab = categorical_vocab
        self._fitted = categorical_vocab is not None

    @classmethod
    def from_training_metadata(cls, metadata: dict) -> FeatureEngineer:
        """Build from training metadata containing categorical vocabularies."""
        vocab = metadata.get("categorical_vocab")
        return cls(categorical_vocab=vocab)

    def transform(self, raw_profile: dict[str, object]) -> pd.DataFrame:
        """Transform a single raw profile dict into a validated feature DataFrame.

        Args:
            raw_profile: Dictionary with raw member feature values.

        Returns:
            Single-row DataFrame with 31 validated features.

        Raises:
            InputSchemaError: If validation fails.
        """
        df = pd.DataFrame([raw_profile])
        return self.transform_batch(df).iloc[[0]]

    def transform_batch(self, raw_profiles: pd.DataFrame) -> pd.DataFrame:
        """Transform a batch of raw profiles into validated feature DataFrames.

        Args:
            raw_profiles: DataFrame with raw member feature values.

        Returns:
            DataFrame with 31 validated features per row.

        Raises:
            InputSchemaError: If validation fails.
        """
        return validate_input(raw_profiles, self._categorical_vocab)

    def fit_from_data(self, df: pd.DataFrame) -> FeatureEngineer:
        """Extract categorical vocabularies from training data.

        Args:
            df: Training DataFrame with all features.

        Returns:
            Self with extracted vocabularies.
        """
        vocab: dict[str, set[str]] = {}
        for col in CATEGORICAL_FEATURES:
            if col in df.columns:
                vocab[col] = set(df[col].dropna().unique())
        self._categorical_vocab = vocab
        self._fitted = True
        return self

    @property
    def categorical_vocab(self) -> dict[str, set[str]] | None:
        """Return the categorical vocabulary mapping."""
        return self._categorical_vocab

    @property
    def fitted(self) -> bool:
        """Whether vocabularies have been extracted from training data."""
        return self._fitted

    def get_metadata(self) -> dict:
        """Return serializable metadata for persistence."""
        return {
            "categorical_vocab": self._categorical_vocab,
            "fitted": self._fitted,
        }
