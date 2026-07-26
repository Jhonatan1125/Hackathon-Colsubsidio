"""Global 60/20/20 stratified split with seed 42.

All 9 models share the exact same train/validation/test partitions.
Split indices and dataset SHA-256 hashes are persisted as metadata.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 42
TRAIN_RATIO = 0.60
VAL_RATIO = 0.20
TEST_RATIO = 0.20


@dataclass(frozen=True)
class SplitResult:
    """Container for split indices and metadata."""

    train_idx: np.ndarray
    val_idx: np.ndarray
    test_idx: np.ndarray
    dataset_hash: str
    metadata: dict = field(default_factory=dict)


def compute_hash(df: pd.DataFrame) -> str:
    """Compute SHA-256 hash of DataFrame for reproducibility tracking."""
    return hashlib.sha256(df.to_json().encode()).hexdigest()


def global_split(
    df: pd.DataFrame,
    target_column: str | None = None,
    seed: int = SEED,
) -> SplitResult:
    """Create a single global 60/20/20 stratified split.

    Args:
        df: Full dataset DataFrame.
        target_column: Column to stratify on. If None, uses random split.
        seed: Random seed for reproducibility.

    Returns:
        SplitResult with train/val/test index arrays and metadata.
    """
    dataset_hash = compute_hash(df)

    if target_column is not None and target_column in df.columns:
        stratify = df[target_column].values
    else:
        stratify = None

    train_idx, temp_idx = train_test_split(
        np.arange(len(df)),
        test_size=(VAL_RATIO + TEST_RATIO),
        random_state=seed,
        stratify=stratify,
    )

    if stratify is not None:
        temp_stratify = df.iloc[temp_idx][target_column].values
    else:
        temp_stratify = None

    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=TEST_RATIO / (VAL_RATIO + TEST_RATIO),
        random_state=seed,
        stratify=temp_stratify,
    )

    metadata = {
        "train_size": len(train_idx),
        "val_size": len(val_idx),
        "test_size": len(test_idx),
        "total_size": len(df),
        "seed": seed,
        "dataset_hash": dataset_hash,
    }

    return SplitResult(
        train_idx=train_idx,
        val_idx=val_idx,
        test_idx=test_idx,
        dataset_hash=dataset_hash,
        metadata=metadata,
    )
