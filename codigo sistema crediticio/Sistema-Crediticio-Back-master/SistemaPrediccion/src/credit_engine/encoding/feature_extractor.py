"""Feature extraction pipeline — raw data to numeric feature vectors.

Composes scikit-learn ColumnTransformer with MultiLabelBinarizer instances
to produce a fixed-width feature vector from person data. Handles Parquet
input where list-type columns are stored as string representations.
"""

from __future__ import annotations

import ast
import json
from typing import TYPE_CHECKING

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import MultiLabelBinarizer, OneHotEncoder, OrdinalEncoder

from .column_definitions import (
    MULTILABEL_COLS,
    NUMERIC_COLS,
    ONEHOT_COLS,
    ORDINAL_COLS,
    ORDINAL_ORDER,
    TARGET_COL,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray


class FeatureExtractor:
    """Encodes person data into a fixed-width numeric feature vector.

    Designed to be fit once on the full training dataset and then reused
    at inference time without re-fitting. Persistable via joblib.

    Handles both raw Python lists and Parquet string-list representations
    (e.g. ``"['A']"`` → ``["A"]``).

    Applies these encoding strategies:
      - Numeric columns: passthrough (no transformation)
      - Categoria afiliacion: one-hot encoding (3 categories)
      - Mora maxima historica: ordinal encoding (4 ordered levels)
      - Multi-label columns: binary indicator per category
    """

    __slots__ = ("_column_transformer", "_multilabel_binarizers", "_feature_count")

    def __init__(self) -> None:
        self._column_transformer: ColumnTransformer | None = None
        self._multilabel_binarizers: dict[str, MultiLabelBinarizer] = {}
        self._feature_count: int | None = None

    # ── Public API ──────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> FeatureExtractor:
        """Learn all categories and encoding parameters from training data."""
        work = self._prepare_dataframe(df)

        self._column_transformer = ColumnTransformer(
            transformers=[
                ("num", "passthrough", list(NUMERIC_COLS)),
                (
                    "onehot",
                    OneHotEncoder(sparse_output=False, handle_unknown="ignore"),
                    list(ONEHOT_COLS),
                ),
                (
                    "ordinal",
                    OrdinalEncoder(categories=ORDINAL_ORDER),
                    list(ORDINAL_COLS),
                ),
            ],
            remainder="drop",
        )
        self._column_transformer.fit(work)

        for col in MULTILABEL_COLS:
            values = work[col].map(self._sanitize_list)
            mlb = MultiLabelBinarizer()
            mlb.fit(values)
            self._multilabel_binarizers[col] = mlb

        self._feature_count = self._compute_feature_count()
        return self

    def transform(self, df: pd.DataFrame) -> NDArray[np.float64]:
        """Encode raw person data into a numeric feature matrix.

        Raises:
            RuntimeError: If called before fitting.
        """
        if self._column_transformer is None:
            raise RuntimeError("FeatureExtractor not fitted. Call fit() first.")

        work = self._prepare_dataframe(df)
        base = self._column_transformer.transform(work)
        parts = [base]

        for col in MULTILABEL_COLS:
            values = work[col].map(self._sanitize_list)
            encoded = self._multilabel_binarizers[col].transform(values)
            parts.append(encoded)

        result = np.hstack(parts)

        if self._feature_count is not None and result.shape[1] != self._feature_count:
            raise ValueError(
                f"Feature count mismatch: expected {self._feature_count}, "
                f"got {result.shape[1]}."
            )

        return result

    def fit_transform(self, df: pd.DataFrame) -> NDArray[np.float64]:
        """Learn categories and encode in a single pass."""
        self.fit(df)
        return self.transform(df)

    # ── Parquet I/O ─────────────────────────────────────────────────────

    def fit_from_parquet(self, path: str) -> FeatureExtractor:
        """Read a Parquet file and fit the encoding pipeline."""
        df = pd.read_parquet(path)
        return self.fit(df)

    def transform_from_parquet(self, input_path: str, output_path: str) -> None:
        """Read a Parquet file, encode, and write the result as a Parquet file.

        The output Parquet contains all encoded feature columns. If the
        target column is present in the input, it is included in the output
        as-is.
        """
        df = pd.read_parquet(input_path)
        encoded = self.transform(df)
        feature_names = self.get_feature_names_out()

        result = pd.DataFrame(encoded, columns=feature_names)

        if TARGET_COL in df.columns:
            result[TARGET_COL] = df[TARGET_COL].values

        result.to_parquet(output_path, index=False)

    # ── Persistence ─────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """Persist the fitted extractor to disk via joblib."""
        if self._column_transformer is None:
            raise RuntimeError("Cannot save: extractor has not been fitted.")

        state = {
            "column_transformer": self._column_transformer,
            "multilabel_binarizers": self._multilabel_binarizers,
            "feature_count": self._feature_count,
        }
        joblib.dump(state, path)

    @classmethod
    def load(cls, path: str) -> FeatureExtractor:
        """Restore a previously saved extractor from disk."""
        state = joblib.load(path)
        instance = cls()
        instance._column_transformer = state["column_transformer"]
        instance._multilabel_binarizers = state["multilabel_binarizers"]
        instance._feature_count = state["feature_count"]
        return instance

    # ── Metadata ────────────────────────────────────────────────────────

    @property
    def feature_count(self) -> int | None:
        """Number of output columns after encoding, or None if not fitted."""
        return self._feature_count

    @property
    def fitted(self) -> bool:
        """Whether this extractor has been fitted on training data."""
        return self._column_transformer is not None

    def get_feature_names_out(self) -> list[str]:
        """Build human-readable column names for the encoded feature matrix."""
        if not self.fitted:
            raise RuntimeError("Extractor not fitted. Call fit() first.")

        names: list[str] = []

        for name, transformer, cols in self._column_transformer.transformers_:  # type: ignore[union-attr]
            if name == "remainder":
                continue
            if hasattr(transformer, "get_feature_names_out"):
                names.extend(transformer.get_feature_names_out())
            else:
                names.extend(cols)

        for col in MULTILABEL_COLS:
            mlb = self._multilabel_binarizers[col]
            names.extend(f"{col}_{category}" for category in mlb.classes_)

        return names

    # ── Internal helpers ────────────────────────────────────────────────

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize the raw DataFrame for encoding.

        Handles Parquet-specific quirks: list columns stored as string
        representations, and categoria_afiliacion needing scalar extraction.
        """
        work = df.copy()

        for col in (ONEHOT_COLS[0], *MULTILABEL_COLS):
            if col in work.columns:
                work[col] = work[col].map(self._parse_list_value)

        self._flatten_categoria(work)
        return work

    @staticmethod
    def _parse_list_value(value: object) -> list[object]:
        """Parse a value that may be a string-list repr back into a Python list.

        Handles three cases:
          - Already a list → returned as-is
          - String like ``"['A', 'B']"`` → parsed via ``ast.literal_eval``
          - ``None`` / NaN → empty list
        """
        if value is None:
            return []
        if isinstance(value, float) and np.isnan(value):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "[]" or stripped == "":
                return []
            try:
                result = ast.literal_eval(stripped)
                if isinstance(result, list):
                    return result
                return [result]
            except (ValueError, SyntaxError):
                try:
                    result = json.loads(stripped)
                    if isinstance(result, list):
                        return result
                    return [result]
                except (json.JSONDecodeError, ValueError):
                    return [stripped]
        return [value] if value else []

    def _flatten_categoria(self, df: pd.DataFrame) -> None:
        """Extract first element from categoria_afiliacion list values."""
        col = ONEHOT_COLS[0]
        if col in df.columns:
            df[col] = df[col].map(
                lambda x: x[0] if isinstance(x, list) and x else x
            )

    def _compute_feature_count(self) -> int:
        """Derive the total output feature count from the fitted encoders."""
        ct = self._column_transformer
        if ct is None:
            return 0

        total = 0
        for name, transformer, cols in ct.transformers_:
            if name == "remainder":
                continue
            if hasattr(transformer, "get_feature_names_out"):
                total += len(transformer.get_feature_names_out())
            else:
                total += len(cols)

        for mlb in self._multilabel_binarizers.values():
            total += len(mlb.classes_)

        return total

    @staticmethod
    def _sanitize_list(value: object) -> list[object]:
        """Normalize multi-label values to a list.

        Replaces None/NaN with an empty list so MultiLabelBinarizer
        receives a valid iterable.
        """
        if value is None:
            return []
        if isinstance(value, float) and np.isnan(value):
            return []
        if isinstance(value, list):
            return value
        return [value]
