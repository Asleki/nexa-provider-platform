"""Ordered data-classification levels for registry metadata."""
from __future__ import annotations

from enum import IntEnum


class RegistryClassificationLevel(IntEnum):
    """Stable sensitivity levels ordered from least to most restrictive."""

    PUBLIC = 10
    INTERNAL = 20
    RESTRICTED = 30
    CONFIDENTIAL = 40
    HIGHLY_RESTRICTED = 50

    @property
    def code(self) -> str:
        """Return the stable lowercase persistence code for this level."""
        return self.name.lower()

    @classmethod
    def from_value(
        cls,
        value: str | "RegistryClassificationLevel",
    ) -> "RegistryClassificationLevel":
        """Normalize an enum member or supported text value into a level."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                "classification level must be text or RegistryClassificationLevel."
            )

        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("classification level cannot be empty.")

        try:
            return cls[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported classification level {value!r}."
            ) from exc

    def __str__(self) -> str:
        return self.code


__all__ = ["RegistryClassificationLevel"]
