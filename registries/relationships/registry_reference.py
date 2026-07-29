"""Immutable reference to one record owned by a registry.

A registry reference carries stable endpoint identity only.  It does not load,
validate, authorise, copy, or transfer ownership of the referenced record.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

_REGISTRY_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
)
_RECORD_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$"
)


class RegistryReferenceError(ValueError):
    """Raised when a registry-reference contract is structurally invalid."""


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        frozen: dict[object, object] = {}
        for key, nested in value.items():
            try:
                hash(key)
            except TypeError as exc:
                raise TypeError("attribute mapping keys must be hashable.") from exc
            frozen[key] = _freeze(nested)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return [_thaw(item) for item in sorted(value, key=repr)]
    return value


def _normalise_required_text(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if not normalised:
        raise RegistryReferenceError(f"{name} cannot be empty.")
    return normalised


@dataclass(frozen=True, slots=True)
class RegistryReference:
    """Stable, immutable identity of one registry-owned record."""

    registry_id: str
    record_id: str
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        registry_id = _normalise_required_text("registry_id", self.registry_id)
        if not _REGISTRY_ID_PATTERN.fullmatch(registry_id):
            raise RegistryReferenceError(
                "registry_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "registry_id", registry_id)

        record_id = _normalise_required_text("record_id", self.record_id)
        if not _RECORD_ID_PATTERN.fullmatch(record_id):
            raise RegistryReferenceError(
                "record_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':', '/' or '-'."
            )
        object.__setattr__(self, "record_id", record_id)

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RegistryReferenceError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalised_key = key.strip()
            if not normalised_key:
                raise RegistryReferenceError("attribute keys cannot be empty.")
            if normalised_key in normalised_attributes:
                raise RegistryReferenceError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalised_attributes[normalised_key] = _freeze(value)
        object.__setattr__(
            self, "attributes", MappingProxyType(normalised_attributes)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deeply detached persistence/transport representation."""
        return {
            "registry_id": self.registry_id,
            "record_id": self.record_id,
            "version": self.version,
            "attributes": _thaw(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RegistryReference":
        """Reconstruct a reference without retaining caller-owned values."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"registry_id", "record_id", "version", "attributes"}
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RegistryReferenceError(f"unknown registry reference fields: {names}.")
        try:
            return cls(**dict(data))
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise RegistryReferenceError("missing required registry reference field.") from exc
            raise


__all__ = ["RegistryReference", "RegistryReferenceError"]
