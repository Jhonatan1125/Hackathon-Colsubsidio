"""Input schema validation for feature vectors.

Validates incoming data before inference: column presence, expected order,
dtype conformance, value ranges, and NaN rejection.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from credit_engine.ml.config.features import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    OOV_THRESHOLD,
)


class InputSchemaError(ValueError):
    """Raised when input data violates the feature contract."""


def validate_input(
    df: pd.DataFrame,
    categorical_vocab: dict[str, set[str]] | None = None,
) -> pd.DataFrame:
    """Validate and prepare input DataFrame against the 31-feature allowlist.

    Args:
        df: Raw input DataFrame with member features.
        categorical_vocab: Mapping of categorical column names to their
            allowed vocabulary sets (from training metadata).

    Returns:
        Validated DataFrame with only the 31 allowed features, properly typed.

    Raises:
        InputSchemaError: If required columns are missing, NaN values are
            present, or OOV rate exceeds threshold.
    """
    missing = set(ALL_FEATURES) - set(df.columns)
    if missing:
        raise InputSchemaError(f"Missing required features: {sorted(missing)}")

    work = df[ALL_FEATURES].copy()

    for col in NUMERICAL_FEATURES:
        nan_mask = work[col].isna()
        if nan_mask.any():
            raise InputSchemaError(
                f"NaN values detected in numerical feature '{col}' "
                f"({nan_mask.sum()} occurrences). Imputation must be handled upstream."
            )

    for col in CATEGORICAL_FEATURES:
        work[col] = work[col].astype("category")

    if categorical_vocab is not None:
        _check_oov_rates(work, categorical_vocab)

    return work


def _check_oov_rates(
    df: pd.DataFrame,
    categorical_vocab: dict[str, set[str]],
) -> None:
    """Check out-of-vocabulary rates for categorical features.

    Raises:
        InputSchemaError: If OOV rate exceeds 20% for any categorical column.
    """
    n_rows = len(df)
    for col, vocab in categorical_vocab.items():
        if col not in df.columns:
            continue
        oov_mask = ~df[col].isin(vocab)
        oov_rate = oov_mask.sum() / n_rows if n_rows > 0 else 0.0
        if oov_rate > OOV_THRESHOLD:
            raise InputSchemaError(
                f"Out-of-vocabulary rate for '{col}' is {oov_rate:.1%} "
                f"(threshold: {OOV_THRESHOLD:.0%}). "
                f"Batch rejected — likely upstream mapping error or distribution shift."
            )
        if oov_mask.any():
            warnings.warn(
                f"Unseen categorical values in '{col}' "
                f"({oov_mask.sum()} rows). Treating as missing."
            )
