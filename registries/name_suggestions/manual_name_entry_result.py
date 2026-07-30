"""Resolved catalogue-backed result for M009.2.1 manual name entry."""
from __future__ import annotations

from dataclasses import dataclass

from registries.names import CanonicalName, NameKind


def _validate_component(
    value: CanonicalName | None,
    expected_kind: NameKind,
    field_name: str,
) -> None:
    if value is None:
        return
    if not isinstance(value, CanonicalName):
        raise TypeError(f"{field_name} must be CanonicalName or None.")
    if value.name_kind is not expected_kind:
        raise ValueError(f"{field_name} must have kind {expected_kind.value}.")


@dataclass(frozen=True, slots=True)
class ManualNameEntryResult:
    """Canonical records resolved from a manual entry request."""

    first_name: CanonicalName
    middle_name: CanonicalName | None = None
    surname: CanonicalName | None = None

    def __post_init__(self) -> None:
        _validate_component(self.first_name, NameKind.FIRST_NAME, "first_name")
        _validate_component(self.middle_name, NameKind.MIDDLE_NAME, "middle_name")
        _validate_component(self.surname, NameKind.SURNAME, "surname")
        runtime_modes = {record.metadata.runtime_mode for record in self.components}
        if len(runtime_modes) != 1:
            raise ValueError("all resolved components must use the same runtime_mode.")

    @property
    def components(self) -> tuple[CanonicalName, ...]:
        return tuple(
            record
            for record in (self.first_name, self.middle_name, self.surname)
            if record is not None
        )

    @property
    def component_count(self) -> int:
        return len(self.components)

    @property
    def rendered_value(self) -> str:
        return " ".join(record.canonical_value for record in self.components)

    @property
    def component_ids(self) -> tuple[str, ...]:
        return tuple(record.name_id for record in self.components)

    @property
    def runtime_mode(self) -> str:
        return self.first_name.metadata.runtime_mode


__all__ = ["ManualNameEntryResult"]
