"""Immutable semantic declaration of a cross-registry relationship type.

Relationship types are extensible value objects rather than a closed global
enum.  Future domains can add semantic types without modifying this foundation.
Direction, cardinality, constraints, and provenance are deliberately deferred.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

_TYPE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
)
_TYPE_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$"
)
_MAX_NAME_LENGTH: Final[int] = 200
_MAX_DESCRIPTION_LENGTH: Final[int] = 2_000


class RelationshipTypeError(ValueError):
    """Raised when a relationship-type contract is structurally invalid."""


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


def _required(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if not normalised:
        raise RelationshipTypeError(f"{name} cannot be empty.")
    return normalised


@dataclass(frozen=True, slots=True)
class RelationshipType:
    """Stable semantic identity and description of one relationship type."""

    relationship_type_id: str
    relationship_type_code: str
    relationship_type_name: str
    description: str = ""
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        type_id = _required("relationship_type_id", self.relationship_type_id)
        if not _TYPE_ID_PATTERN.fullmatch(type_id):
            raise RelationshipTypeError(
                "relationship_type_id must start with a letter or digit and contain "
                "only letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "relationship_type_id", type_id)

        code = _required("relationship_type_code", self.relationship_type_code).upper()
        if not _TYPE_CODE_PATTERN.fullmatch(code):
            raise RelationshipTypeError(
                "relationship_type_code must be a hierarchical dotted code with "
                "at least two uppercase semantic segments."
            )
        object.__setattr__(self, "relationship_type_code", code)

        name = _required("relationship_type_name", self.relationship_type_name)
        if len(name) > _MAX_NAME_LENGTH:
            raise RelationshipTypeError(
                f"relationship_type_name cannot exceed {_MAX_NAME_LENGTH} characters."
            )
        object.__setattr__(self, "relationship_type_name", name)

        if not isinstance(self.description, str):
            raise TypeError("description must be text.")
        description = self.description.strip()
        if len(description) > _MAX_DESCRIPTION_LENGTH:
            raise RelationshipTypeError(
                f"description cannot exceed {_MAX_DESCRIPTION_LENGTH} characters."
            )
        object.__setattr__(self, "description", description)

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RelationshipTypeError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalised_key = key.strip()
            if not normalised_key:
                raise RelationshipTypeError("attribute keys cannot be empty.")
            if normalised_key in normalised_attributes:
                raise RelationshipTypeError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalised_attributes[normalised_key] = _freeze(value)
        object.__setattr__(self, "attributes", MappingProxyType(normalised_attributes))

    def to_dict(self) -> dict[str, object]:
        return {
            "relationship_type_id": self.relationship_type_id,
            "relationship_type_code": self.relationship_type_code,
            "relationship_type_name": self.relationship_type_name,
            "description": self.description,
            "version": self.version,
            "attributes": _thaw(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipType":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "relationship_type_id",
            "relationship_type_code",
            "relationship_type_name",
            "description",
            "version",
            "attributes",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipTypeError(f"unknown relationship type fields: {names}.")
        try:
            return cls(**dict(data))
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise RelationshipTypeError("missing required relationship type field.") from exc
            raise


__all__ = ["RelationshipType", "RelationshipTypeError"]
