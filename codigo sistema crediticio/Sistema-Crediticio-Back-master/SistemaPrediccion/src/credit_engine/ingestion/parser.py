"""Parsers for extracting person IDs from uploaded CSV and TXT files."""

import csv
import logging
from io import StringIO

logger = logging.getLogger(__name__)


def _extract_ids_from_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def parse_csv(content: str | bytes) -> list[str]:
    """Parse person IDs from CSV content.

    Reads all non-empty cells from every row and returns them as a
    flat list of stripped strings.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    reader = csv.reader(StringIO(content))
    rows = list(reader)
    ids = [cell.strip() for row in rows for cell in row if cell.strip()]

    logger.info("CSV parsed: %d rows, %d total cells, %d non-empty IDs", len(rows), sum(len(r) for r in rows), len(ids))
    if ids:
        logger.debug("First 5 IDs: %s", ids[:5])

    return ids


def parse_txt(content: str | bytes) -> list[str]:
    """Parse person IDs from plain text content (one ID per line)."""
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")

    ids = _extract_ids_from_lines(content.splitlines())
    logger.info("TXT parsed: %d lines, %d non-empty IDs", len(content.splitlines()), len(ids))
    if ids:
        logger.debug("First 5 IDs: %s", ids[:5])

    return ids
