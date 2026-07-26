"""Validation, sanitization, and deduplication of person IDs.

Two ID formats are accepted at the ingestion boundary:

- **Colombian cédulas** — 5 to 11 digits; dots and surrounding whitespace
  are tolerated and removed during sanitization (e.g. ``"12.345.678"``).
- **Synthetic member IDs** — ``"P"`` followed by digits (e.g. ``"P00123"``),
  the format used by the Data layer's synthetic population and by the
  ``ROOT_IMPLEMENTATION.md`` §8 API contract example (``"P001"``).

Batch bounds follow ``ROOT_IMPLEMENTATION.md`` §1/§8: batch processing
accepts **10 to 2,000 IDs**. Both bounds are parameterizable for callers
with different needs (e.g. internal tooling).
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MIN_BATCH_SIZE = 10
MAX_BATCH_SIZE = 2_000

_CEDULA_MIN_DIGITS = 5
_CEDULA_MAX_DIGITS = 11
_SYNTHETIC_MAX_DIGITS = 11


@dataclass
class ValidationResult:
    """Result of validating a list of person IDs.

    Attributes:
        valid_ids: Sanitized IDs that passed validation and are unique.
        invalid_ids: Raw IDs that failed format validation.
        duplicate_ids: Sanitized IDs that appeared more than once.
    """

    valid_ids: list[str] = field(default_factory=list)
    invalid_ids: list[str] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)


def sanitize_id(raw: str) -> str:
    """Normalize a raw ID string: remove dots, strip whitespace, uppercase.

    Uppercasing normalizes synthetic IDs (``"p001"`` → ``"P001"``) and is a
    no-op for purely numeric cédulas.
    """
    return raw.replace(".", "").strip().upper()


def _is_ascii_digits(value: str) -> bool:
    """True if value is non-empty and contains only ASCII digits 0-9.

    ``str.isdigit()`` alone also accepts non-ASCII digits (e.g. Arabic-Indic
    ``"١٢٣٤٥"``) and superscripts (``"¹²³"``), which would validate here but
    break downstream consumers — the ASCII guard closes that hole.
    """
    return value.isascii() and value.isdigit()


def is_valid_colombian_id(cleaned: str) -> bool:
    """Check whether a sanitized string is a plausible Colombian cédula.

    Returns True if the string consists entirely of ASCII digits and has
    between 5 and 11 characters.
    """
    return _is_ascii_digits(cleaned) and _CEDULA_MIN_DIGITS <= len(cleaned) <= _CEDULA_MAX_DIGITS


def is_valid_synthetic_id(cleaned: str) -> bool:
    """Check whether a sanitized string is a synthetic member ID.

    Synthetic IDs are ``"P"`` followed by 1 to 11 digits (e.g. ``"P001"``,
    ``"P00123"``) — the format produced by the Data layer's synthetic
    population generator.
    """
    return (
        cleaned.startswith("P")
        and _is_ascii_digits(cleaned[1:])
        and 1 <= len(cleaned) - 1 <= _SYNTHETIC_MAX_DIGITS
    )


def is_valid_person_id(cleaned: str) -> bool:
    """Check whether a sanitized string is an accepted person ID (either format)."""
    return is_valid_colombian_id(cleaned) or is_valid_synthetic_id(cleaned)


def validate_person_ids(
    raw_ids: list[str],
    *,
    min_batch_size: int = MIN_BATCH_SIZE,
    max_batch_size: int = MAX_BATCH_SIZE,
) -> ValidationResult:
    """Validate, sanitize, and deduplicate a list of raw person IDs.

    Each raw ID is sanitized (dots removed, stripped, uppercased) and
    checked against both accepted formats (cédula or synthetic ID).
    Duplicates are detected within the same batch. The number of valid
    IDs must fall within [min_batch_size, max_batch_size] — the
    ``ROOT_IMPLEMENTATION.md`` batch contract is 10 to 2,000 IDs.

    Args:
        raw_ids: Raw person ID strings to validate.
        min_batch_size: Minimum number of valid IDs required per batch.
            Pass 0 to disable the lower bound.
        max_batch_size: Maximum number of valid IDs allowed per batch.

    Returns:
        ValidationResult with categorized results.

    Raises:
        ValueError: If the number of valid IDs exceeds max_batch_size or
            falls below min_batch_size.
    """
    result = ValidationResult()
    seen: set[str] = set()

    for raw in raw_ids:
        cleaned = sanitize_id(raw)

        if not is_valid_person_id(cleaned):
            result.invalid_ids.append(raw)
            continue

        if cleaned in seen:
            result.duplicate_ids.append(cleaned)
            continue

        seen.add(cleaned)
        result.valid_ids.append(cleaned)

    if len(result.valid_ids) > max_batch_size:
        logger.warning(
            "Batch size %d exceeds limit of %d — rejecting",
            len(result.valid_ids), max_batch_size,
        )
        raise ValueError(f"Batch size {len(result.valid_ids)} exceeds limit of {max_batch_size}")

    if len(result.valid_ids) < min_batch_size:
        logger.warning(
            "Batch size %d below minimum of %d — rejecting",
            len(result.valid_ids), min_batch_size,
        )
        raise ValueError(
            f"Batch size {len(result.valid_ids)} is below the minimum of {min_batch_size} valid IDs"
        )

    logger.info(
        "Validation: %d valid, %d invalid, %d duplicates of %d raw IDs",
        len(result.valid_ids), len(result.invalid_ids),
        len(result.duplicate_ids), len(raw_ids),
    )

    return result
