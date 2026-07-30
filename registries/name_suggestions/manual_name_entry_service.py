"""Catalogue-backed resolver for M009.2.1 manual name entry."""
from __future__ import annotations

from registries.names import (
    CanonicalName,
    NameKind,
    NameRepository,
    NameSearchQuery,
    NameSearchService,
)

from .manual_name_entry import ManualNameEntry
from .manual_name_entry_errors import (
    ManualNameComponentAmbiguousError,
    ManualNameComponentNotFoundError,
)
from .manual_name_entry_result import ManualNameEntryResult


class ManualNameEntryService:
    """Resolve entered values to active canonical catalogue records."""

    def __init__(self, repository: NameRepository) -> None:
        if not isinstance(repository, NameRepository):
            raise TypeError("repository must implement NameRepository.")
        self._search = NameSearchService(repository)

    def resolve(self, entry: ManualNameEntry) -> ManualNameEntryResult:
        if not isinstance(entry, ManualNameEntry):
            raise TypeError("entry must be ManualNameEntry.")

        first_name = self._resolve_component(
            entry.first_name, NameKind.FIRST_NAME, entry.runtime_mode
        )
        middle_name = (
            self._resolve_component(
                entry.middle_name, NameKind.MIDDLE_NAME, entry.runtime_mode
            )
            if entry.middle_name is not None
            else None
        )
        surname = (
            self._resolve_component(entry.surname, NameKind.SURNAME, entry.runtime_mode)
            if entry.surname is not None
            else None
        )
        return ManualNameEntryResult(first_name, middle_name, surname)

    def _resolve_component(
        self,
        value: str,
        name_kind: NameKind,
        runtime_mode: str,
    ) -> CanonicalName:
        result = self._search.search(
            NameSearchQuery(
                text=value,
                name_kind=name_kind,
                runtime_mode=runtime_mode,
                exact=True,
                limit=2,
            )
        )
        if result.total == 0:
            raise ManualNameComponentNotFoundError(
                f"active {name_kind.value} {value!r} was not found in "
                f"runtime_mode {runtime_mode!r}."
            )
        if result.total > 1:
            raise ManualNameComponentAmbiguousError(
                f"active {name_kind.value} {value!r} resolved ambiguously."
            )
        return result.records[0]


__all__ = ["ManualNameEntryService"]
