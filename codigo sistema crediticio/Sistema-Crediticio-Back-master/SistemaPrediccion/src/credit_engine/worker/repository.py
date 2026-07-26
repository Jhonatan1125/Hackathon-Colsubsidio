"""In-memory person repository — local stand-in for the ``database/`` package.

Satisfies the ``PersonRepository`` Protocol. When ``database/`` lands
(synthetic population or real member records), it plugs into the worker
through the same Protocol without touching pipeline code.
"""

from __future__ import annotations

from typing import Any


class InMemoryPersonRepository:
    """Dictionary-backed person store keyed by sanitized person ID."""

    def __init__(self, persons: dict[str, dict[str, Any]] | None = None) -> None:
        self._persons: dict[str, dict[str, Any]] = dict(persons) if persons else {}

    def add_person(self, person_id: str, data: dict[str, Any]) -> None:
        """Insert or replace a person record."""
        self._persons[person_id] = dict(data)

    def get_person(self, person_id: str) -> dict[str, Any] | None:
        """Return a copy of the person record, or None if unknown."""
        person = self._persons.get(person_id)
        return dict(person) if person is not None else None
