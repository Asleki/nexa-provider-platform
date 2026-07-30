"""Immutable manual-entry request for the M009.2 atomic composition layer."""
from __future__ import annotations

from dataclasses import dataclass

from registries.names import normalize_name_value


def _optional_component(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be text or None.")
    if not value.strip():
        return None
    return normalize_name_value(value)


def _runtime_mode(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("runtime_mode must be text.")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("runtime_mode cannot be empty.")
    return normalized


@dataclass(frozen=True, slots=True)
class ManualNameEntry:
    """Developer-entered atomic components to resolve against M009.1."""

    first_name: str
    middle_name: str | None = None
    surname: str | None = None
    runtime_mode: str = "simulation"

    def __post_init__(self) -> None:
        if not isinstance(self.first_name, str):
            raise TypeError("first_name must be text.")
        object.__setattr__(self, "first_name", normalize_name_value(self.first_name))
        object.__setattr__(
            self, "middle_name", _optional_component(self.middle_name, "middle_name")
        )
        object.__setattr__(
            self, "surname", _optional_component(self.surname, "surname")
        )
        object.__setattr__(self, "runtime_mode", _runtime_mode(self.runtime_mode))

    @property
    def component_count(self) -> int:
        return 1 + int(self.middle_name is not None) + int(self.surname is not None)

    @property
    def rendered_value(self) -> str:
        return " ".join(
            value
            for value in (self.first_name, self.middle_name, self.surname)
            if value is not None
        )


__all__ = ["ManualNameEntry"]
