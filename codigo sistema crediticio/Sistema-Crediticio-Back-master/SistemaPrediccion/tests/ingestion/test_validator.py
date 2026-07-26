import pytest

from credit_engine.ingestion.validator import (
    MAX_BATCH_SIZE,
    MIN_BATCH_SIZE,
    ValidationResult,
    is_valid_colombian_id,
    is_valid_person_id,
    is_valid_synthetic_id,
    sanitize_id,
    validate_person_ids,
)


class TestSanitizeId:
    def test_removes_dots(self):
        assert sanitize_id("12.345.678") == "12345678"

    def test_trims_whitespace(self):
        assert sanitize_id("  12345678  ") == "12345678"

    def test_removes_dots_and_trims_whitespace(self):
        assert sanitize_id(" 12.345.678 ") == "12345678"

    def test_preserves_valid_id(self):
        assert sanitize_id("12345678") == "12345678"

    def test_uppercases_synthetic_prefix(self):
        assert sanitize_id("p00123") == "P00123"

    def test_handles_empty_string(self):
        assert sanitize_id("") == ""


class TestIsValidColombianId:
    @pytest.mark.parametrize(
        "cleaned, expected",
        [
            ("12345", True),
            ("1234567890", True),
            ("9999999999", True),
            ("1234", False),
            ("123456789012", False),  # 12 digits — above cédula bound
            ("", False),
            ("abcde", False),
            ("1234a", False),
            ("12.345", False),
            ("١٢٣٤٥", False),  # Arabic-Indic digits pass str.isdigit() but are not valid
            ("¹²³⁴⁵", False),  # superscripts pass str.isdigit() but break int() downstream
        ],
    )
    def test_validates_format(self, cleaned: str, expected: bool):
        assert is_valid_colombian_id(cleaned) == expected

    def test_minimum_length_is_five(self):
        assert is_valid_colombian_id("12345") is True
        assert is_valid_colombian_id("1234") is False


class TestIsValidSyntheticId:
    @pytest.mark.parametrize(
        "cleaned, expected",
        [
            ("P001", True),
            ("P00123", True),
            ("P1", True),
            ("P", False),
            ("PABC", False),
            ("12345", False),
            ("P123456789012", False),  # 12 digits — above bound
            ("", False),
        ],
    )
    def test_validates_format(self, cleaned: str, expected: bool):
        assert is_valid_synthetic_id(cleaned) == expected


class TestIsValidPersonId:
    def test_accepts_cedula(self):
        assert is_valid_person_id("12345678") is True

    def test_accepts_synthetic_id(self):
        assert is_valid_person_id("P00123") is True

    def test_rejects_garbage(self):
        assert is_valid_person_id("abc") is False
        assert is_valid_person_id("") is False


class TestValidatePersonIds:
    def test_default_bounds_match_root_contract(self):
        assert MIN_BATCH_SIZE == 10
        assert MAX_BATCH_SIZE == 2_000

    def test_returns_valid_ids(self):
        result = validate_person_ids(["12345678", "87654321"], min_batch_size=1)
        assert result.valid_ids == ["12345678", "87654321"]
        assert result.invalid_ids == []
        assert result.duplicate_ids == []

    def test_accepts_synthetic_ids(self):
        result = validate_person_ids(["P00123", "p001"], min_batch_size=1)
        assert result.valid_ids == ["P00123", "P001"]
        assert result.invalid_ids == []

    def test_identifies_invalid_ids(self):
        result = validate_person_ids(["abc", "12345", "xyz"], min_batch_size=1)
        assert result.valid_ids == ["12345"]
        assert result.invalid_ids == ["abc", "xyz"]
        assert result.duplicate_ids == []

    def test_detects_duplicates(self):
        result = validate_person_ids(["12345678", "12345678", "87654321"], min_batch_size=1)
        assert result.valid_ids == ["12345678", "87654321"]
        assert result.invalid_ids == []
        assert result.duplicate_ids == ["12345678"]

    def test_sanitizes_before_validation(self):
        result = validate_person_ids(["12.345.678"], min_batch_size=1)
        assert result.valid_ids == ["12345678"]

    def test_empty_list_raises_below_minimum(self):
        with pytest.raises(ValueError, match="below the minimum"):
            validate_person_ids([])

    def test_min_batch_size_zero_allows_empty(self):
        result = validate_person_ids([], min_batch_size=0)
        assert result.valid_ids == []
        assert result.invalid_ids == []
        assert result.duplicate_ids == []

    def test_all_invalid_yields_empty_valid_ids(self):
        result = validate_person_ids(["abc", "12", "!!!"], min_batch_size=0)
        assert result.valid_ids == []
        assert len(result.invalid_ids) == 3

    def test_returns_validation_result_type(self):
        result = validate_person_ids(["12345678"], min_batch_size=1)
        assert isinstance(result, ValidationResult)

    def test_raises_when_below_min_batch_size(self):
        ids = [f"{10000 + i}" for i in range(9)]
        with pytest.raises(ValueError, match="below the minimum"):
            validate_person_ids(ids)

    def test_allows_exactly_min_batch_size(self):
        ids = [f"{10000 + i}" for i in range(10)]
        result = validate_person_ids(ids)
        assert len(result.valid_ids) == 10

    def test_raises_when_exceeds_batch_size(self):
        ids = [f"{10000 + i}" for i in range(2001)]
        with pytest.raises(ValueError, match="exceeds limit"):
            validate_person_ids(ids)

    def test_allows_exactly_max_batch_size(self):
        ids = [f"{10000 + i}" for i in range(2000)]
        result = validate_person_ids(ids)
        assert len(result.valid_ids) == 2000
        assert len(result.invalid_ids) == 0

    def test_custom_max_batch_size_raises(self):
        ids = ["12345", "23456", "34567"]
        with pytest.raises(ValueError, match="exceeds limit"):
            validate_person_ids(ids, max_batch_size=2)

    def test_duplicate_and_invalid_mixed(self):
        result = validate_person_ids(["12345", "abc", "12345", "12", "67890"], min_batch_size=1)
        assert result.valid_ids == ["12345", "67890"]
        assert result.invalid_ids == ["abc", "12"]
        assert result.duplicate_ids == ["12345"]
