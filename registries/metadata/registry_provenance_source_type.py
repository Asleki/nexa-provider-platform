"""Canonical immediate-source types for registry provenance metadata.

The enum identifies the immediate origin route represented by one
``RegistryProvenance`` declaration.  It does not model a complete lineage
 graph, source trust, ownership, licensing, audit history, or data quality.
"""
from __future__ import annotations

from enum import Enum


class RegistryProvenanceSourceType(str, Enum):
    """Stable persisted identities for immediate registry provenance."""

    HUMAN = "human"
    INSTITUTION = "institution"
    SYSTEM = "system"
    IMPORT = "import"
    SIMULATION_GENERATOR = "simulation_generator"
    DERIVED = "derived"
    UNKNOWN = "unknown"

    @classmethod
    def from_value(
        cls,
        value: "RegistryProvenanceSourceType | str",
    ) -> "RegistryProvenanceSourceType":
        """Return a canonical source type from an enum member or text value."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                "provenance source type must be text or "
                "RegistryProvenanceSourceType."
            )
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("provenance source type cannot be empty.")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported provenance source type {value!r}."
            ) from exc

    def __str__(self) -> str:
        return self.value


__all__ = ["RegistryProvenanceSourceType"]
