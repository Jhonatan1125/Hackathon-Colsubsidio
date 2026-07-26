import numpy as np
import pandas as pd
import pytest

from credit_engine.encoding import (
    EXCLUDED_COLS,
    MULTILABEL_COLS,
    NUMERIC_COLS,
    ONEHOT_COLS,
    ORDINAL_COLS,
    TARGET_COL,
)
from credit_engine.encoding.feature_extractor import FeatureExtractor


def _make_sample_df(rows: int = 5) -> pd.DataFrame:
    _onehot_values = [["A"], ["B"], ["C"], ["A"], ["B"]]
    _ordinal_values = ["0_DIAS", "30_DIAS", "60_DIAS", "90_MAS_DIAS", "0_DIAS"]
    _target_values = ["CREDITO_EDUCATIVO", "CUPO_ROTATIVO", "COMPRA_CARTERA", "CREDITO_VIVIENDA", "LIBRANZA"]
    _multilabel_values = [
        [["admin", "ventas"], ["soporte"], [], ["admin"], ["ventas"]],
        [[], ["deporte"], ["lectura", "viajes"], ["lectura"], ["deporte", "viajes"]],
        [["online"], [], [], ["online", "presencial"], ["presencial"]],
        [[], ["cumpleaños"], ["aniversario"], [], ["aniversario", "cumpleaños"]],
        [["hijos"], ["pareja"], [], ["hijos", "pareja"], ["pareja"]],
        [["credito_vivienda"], [], ["libranza", "rotativo"], ["credito_vivienda"], []],
    ]

    def _cycle(seq: list[object], n: int) -> list[object]:
        return [(seq[i % len(seq)]) for i in range(n)]

    data: dict[str, list[object]] = {}

    for col in NUMERIC_COLS:
        data[col] = [float(i + 1) for i in range(rows)]

    data[ONEHOT_COLS[0]] = _cycle(_onehot_values, rows)
    data[ORDINAL_COLS[0]] = _cycle(_ordinal_values, rows)
    data[TARGET_COL] = _cycle(_target_values, rows)

    for idx, col in enumerate(MULTILABEL_COLS):
        data[col] = _cycle(_multilabel_values[idx], rows)

    for col in EXCLUDED_COLS:
        data[col] = [f"{col}_{i}" for i in range(rows)]

    return pd.DataFrame(data)


class TestFeatureExtractorInit:
    def test_not_fitted_after_construction(self):
        extractor = FeatureExtractor()
        assert not extractor.fitted

    def test_feature_count_is_none_before_fit(self):
        extractor = FeatureExtractor()
        assert extractor.feature_count is None


class TestFeatureExtractorFit:
    def test_sets_fitted_to_true(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        assert extractor.fitted

    def test_sets_feature_count(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        assert extractor.feature_count is not None
        assert extractor.feature_count > 0

    def test_returns_self_for_chaining(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        result = extractor.fit(df)
        assert result is extractor

    def test_feature_count_is_stable_on_repeated_calls(self):
        df = _make_sample_df(rows=20)
        extractor = FeatureExtractor()
        extractor.fit(df)
        assert extractor.feature_count is not None
        assert extractor.feature_count > 0
        first_count = extractor.feature_count
        extractor.fit(df)
        assert extractor.feature_count == first_count

    def test_learns_all_categories_in_multilabel_columns(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)

        for col in MULTILABEL_COLS:
            assert col in extractor._multilabel_binarizers
            assert len(extractor._multilabel_binarizers[col].classes_) > 0

    def test_handles_single_row(self):
        df = _make_sample_df(rows=1)
        extractor = FeatureExtractor()
        extractor.fit(df)
        assert extractor.fitted
        assert extractor.feature_count is not None

    def test_handles_none_in_multilabel_columns(self):
        df = _make_sample_df(rows=3)
        df[MULTILABEL_COLS[1]] = [None, ["deporte"], None]
        extractor = FeatureExtractor()
        extractor.fit(df)
        assert extractor.fitted

    def test_handles_nan_in_multilabel_columns(self):
        df = _make_sample_df(rows=3)
        df[MULTILABEL_COLS[1]] = [float("nan"), ["deporte"], float("nan")]
        extractor = FeatureExtractor()
        extractor.fit(df)
        assert extractor.fitted


class TestFeatureExtractorTransform:
    def test_raises_runtime_error_when_not_fitted(self):
        extractor = FeatureExtractor()
        df = _make_sample_df()
        with pytest.raises(RuntimeError, match="not fitted"):
            extractor.transform(df)

    def test_output_is_numpy_array(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        result = extractor.transform(df)
        assert isinstance(result, np.ndarray)

    def test_output_is_two_dimensional(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        result = extractor.transform(df)
        assert result.ndim == 2

    def test_row_count_matches_input(self):
        df = _make_sample_df(rows=7)
        extractor = FeatureExtractor()
        extractor.fit(df)
        result = extractor.transform(df)
        assert result.shape[0] == 7

    def test_column_count_matches_feature_count(self):
        df = _make_sample_df(rows=10)
        extractor = FeatureExtractor()
        extractor.fit(df)
        result = extractor.transform(df)
        assert result.shape[1] == extractor.feature_count

    def test_output_is_dense_not_sparse(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        result = extractor.transform(df)
        assert isinstance(result, np.ndarray)

    def test_all_values_are_finite(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        result = extractor.transform(df)
        assert np.all(np.isfinite(result))

    def test_numeric_columns_pass_through_unchanged(self):
        df = _make_sample_df(rows=3)
        extractor = FeatureExtractor()
        extractor.fit(df)

        numeric_col_index = 0
        result = extractor.transform(df)
        for i in range(3):
            assert result[i, numeric_col_index] == pytest.approx(float(i + 1))

    def test_handles_unknown_categories_gracefully(self):
        df_train = _make_sample_df(rows=3)
        extractor = FeatureExtractor()
        extractor.fit(df_train)

        df_infer = _make_sample_df(rows=1)
        df_infer[ONEHOT_COLS[0]] = [["Z"]]

        result = extractor.transform(df_infer)
        assert result.shape[1] == extractor.feature_count

    def test_handles_empty_multilabel_at_inference(self):
        df_train = _make_sample_df(rows=3)
        extractor = FeatureExtractor()
        extractor.fit(df_train)

        df_infer = _make_sample_df(rows=1)
        for col in MULTILABEL_COLS:
            df_infer[col] = [[]]
        df_infer[ONEHOT_COLS[0]] = [["A"]]
        df_infer[ORDINAL_COLS[0]] = "0_DIAS"

        result = extractor.transform(df_infer)
        assert result.shape[1] == extractor.feature_count

    def test_handles_single_row_inference(self):
        df = _make_sample_df(rows=5)
        extractor = FeatureExtractor()
        extractor.fit(df)

        single = _make_sample_df(rows=1)
        result = extractor.transform(single)
        assert result.shape == (1, extractor.feature_count)

    def test_consistent_output_shape_across_calls(self):
        df = _make_sample_df(rows=10)
        extractor = FeatureExtractor()
        extractor.fit(df)

        result1 = extractor.transform(df.head(3))
        result2 = extractor.transform(df.tail(4))
        assert result1.shape[1] == result2.shape[1] == extractor.feature_count

    def test_excluded_columns_are_dropped(self):
        df = _make_sample_df(rows=3)
        extractor = FeatureExtractor()
        extractor.fit(df)

        df_with_extra = df.copy()
        df_with_extra["random_column"] = "should_be_dropped"

        result = extractor.transform(df_with_extra)
        assert result.shape[1] == extractor.feature_count


class TestFeatureExtractorFitTransform:
    def test_returns_numpy_array(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        result = extractor.fit_transform(df)
        assert isinstance(result, np.ndarray)

    def test_fits_and_transforms_in_one_call(self):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        result = extractor.fit_transform(df)
        assert extractor.fitted
        assert result.shape[1] == extractor.feature_count

    def test_same_result_as_separate_fit_and_transform(self):
        df = _make_sample_df(rows=10)
        e1 = FeatureExtractor()
        result1 = e1.fit_transform(df)

        e2 = FeatureExtractor()
        e2.fit(df)
        result2 = e2.transform(df)

        np.testing.assert_array_equal(result1, result2)


class TestFeatureExtractorSaveLoad:
    def test_save_raises_when_not_fitted(self, tmp_path):
        extractor = FeatureExtractor()
        path = tmp_path / "extractor.joblib"
        with pytest.raises(RuntimeError, match="not been fitted"):
            extractor.save(str(path))

    def test_roundtrip_preserves_feature_count(self, tmp_path):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)
        original_count = extractor.feature_count

        path = tmp_path / "extractor.joblib"
        extractor.save(str(path))

        loaded = FeatureExtractor.load(str(path))
        assert loaded.feature_count == original_count

    def test_roundtrip_preserves_fitted_state(self, tmp_path):
        df = _make_sample_df()
        extractor = FeatureExtractor()
        extractor.fit(df)

        path = tmp_path / "extractor.joblib"
        extractor.save(str(path))

        loaded = FeatureExtractor.load(str(path))
        assert loaded.fitted

    def test_roundtrip_produces_identical_output(self, tmp_path):
        df = _make_sample_df(rows=10)
        extractor = FeatureExtractor()
        extractor.fit(df)
        original_result = extractor.transform(df)

        path = tmp_path / "extractor.joblib"
        extractor.save(str(path))

        loaded = FeatureExtractor.load(str(path))
        loaded_result = loaded.transform(df)

        np.testing.assert_array_almost_equal(original_result, loaded_result)

    def test_loaded_extractor_handles_inference_without_refit(self, tmp_path):
        df_train = _make_sample_df(rows=10)
        extractor = FeatureExtractor()
        extractor.fit(df_train)

        path = tmp_path / "extractor.joblib"
        extractor.save(str(path))

        loaded = FeatureExtractor.load(str(path))
        df_infer = _make_sample_df(rows=2)
        result = loaded.transform(df_infer)
        assert result.shape[1] == loaded.feature_count

    def test_save_and_load_with_complex_multilabel_data(self, tmp_path):
        df = _make_sample_df(rows=8)
        extractor = FeatureExtractor()
        extractor.fit(df)

        path = tmp_path / "extractor.joblib"
        extractor.save(str(path))

        loaded = FeatureExtractor.load(str(path))
        assert loaded.transform(df).shape == extractor.transform(df).shape


class TestFeatureExtractorSanitizeList:
    def test_none_returns_empty_list(self):
        result = FeatureExtractor._sanitize_list(None)
        assert result == []

    def test_nan_returns_empty_list(self):
        result = FeatureExtractor._sanitize_list(float("nan"))
        assert result == []

    def test_list_returns_same_list(self):
        result = FeatureExtractor._sanitize_list(["a", "b"])
        assert result == ["a", "b"]

    def test_empty_list_returns_empty_list(self):
        result = FeatureExtractor._sanitize_list([])
        assert result == []

    def test_scalar_wraps_in_list(self):
        result = FeatureExtractor._sanitize_list("single_value")
        assert result == ["single_value"]

    def test_integer_scalar_wraps_in_list(self):
        result = FeatureExtractor._sanitize_list(42)
        assert result == [42]


class TestFeatureExtractorFlattenListColumn:
    def test_extracts_first_element_from_list(self):
        extractor = FeatureExtractor()
        col = ONEHOT_COLS[0]
        df = pd.DataFrame({col: [["A"], ["B"], ["C"]]})
        extractor._flatten_list_column(df)
        assert list(df[col]) == ["A", "B", "C"]

    def test_passes_through_non_list_values(self):
        extractor = FeatureExtractor()
        col = ONEHOT_COLS[0]
        df = pd.DataFrame({col: ["A", "B", "C"]})
        extractor._flatten_list_column(df)
        assert list(df[col]) == ["A", "B", "C"]

    def test_handles_empty_list(self):
        extractor = FeatureExtractor()
        col = ONEHOT_COLS[0]
        df = pd.DataFrame({col: [["A"], [], ["C"]]})
        extractor._flatten_list_column(df)
        assert list(df[col]) == ["A", [], "C"]

    def test_noop_when_column_missing(self):
        extractor = FeatureExtractor()
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        extractor._flatten_list_column(df)
        assert "other_col" in df.columns


class TestFeatureExtractorEdgeCases:
    def test_empty_dataframe_fit(self):
        df = _make_sample_df(rows=0)
        extractor = FeatureExtractor()
        with pytest.raises(ValueError):
            extractor.fit(df)

    def test_consistent_output_when_categories_in_train_match_infer(self):
        df = _make_sample_df(rows=10)
        extractor = FeatureExtractor()
        extractor.fit(df)

        result_same = extractor.transform(df)
        assert result_same.shape[1] == extractor.feature_count

    def test_new_multilabel_categories_at_inference_produce_zeros(self):
        df_train = _make_sample_df(rows=4)
        extractor = FeatureExtractor()
        extractor.fit(df_train)

        df_infer = _make_sample_df(rows=1)
        df_infer[MULTILABEL_COLS[1]] = [["categoria_nunca_vista"]]

        result = extractor.transform(df_infer)
        assert result.shape[1] == extractor.feature_count
