"""Immutable declaration of one cross-registry relationship instance.

The contract identifies a typed source-to-target link.  It does not resolve
endpoints, enforce direction or cardinality, persist data, publish events, or
apply domain consequences.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from .registry_reference import RegistryReference
from .relationship_type import RelationshipType

_RELATIONSHIP_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
)
_RUNTIME_MODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_-]{0,63}$"
)


class RelationshipDefinitionError(ValueError):
    """Raised when a relationship-definition contract is invalid."""


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
        raise RelationshipDefinitionError(f"{name} cannot be empty.")
    return normalised


@dataclass(frozen=True, slots=True)
class RelationshipDefinition:
    """One stable, typed and runtime-separated relationship instance."""

    relationship_id: str
    relationship_type: RelationshipType
    source: RegistryReference
    target: RegistryReference
    runtime_mode: str
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        relationship_id = _required("relationship_id", self.relationship_id)
        if not _RELATIONSHIP_ID_PATTERN.fullmatch(relationship_id):
            raise RelationshipDefinitionError(
                "relationship_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "relationship_id", relationship_id)

        if not isinstance(self.relationship_type, RelationshipType):
            raise TypeError("relationship_type must be a RelationshipType.")
        if not isinstance(self.source, RegistryReference):
            raise TypeError("source must be a RegistryReference.")
        if not isinstance(self.target, RegistryReference):
            raise TypeError("target must be a RegistryReference.")

        runtime_mode = _required("runtime_mode", self.runtime_mode).lower()
        if not _RUNTIME_MODE_PATTERN.fullmatch(runtime_mode):
            raise RelationshipDefinitionError(
                "runtime_mode must start with a lowercase letter and contain only "
                "lowercase letters, digits, '_' or '-'."
            )
        object.__setattr__(self, "runtime_mode", runtime_mode)

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RelationshipDefinitionError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalised_key = key.strip()
            if not normalised_key:
                raise RelationshipDefinitionError("attribute keys cannot be empty.")
            if normalised_key in normalised_attributes:
                raise RelationshipDefinitionError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalised_attributes[normalised_key] = _freeze(value)
        object.__setattr__(self, "attributes", MappingProxyType(normalised_attributes))

    def to_dict(self) -> dict[str, object]:
        return {
            "relationship_id": self.relationship_id,
            "relationship_type": self.relationship_type.to_dict(),
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "runtime_mode": self.runtime_mode,
            "version": self.version,
            "attributes": _thaw(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipDefinition":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "relationship_id",
            "relationship_type",
            "source",
            "target",
            "runtime_mode",
            "version",
            "attributes",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipDefinitionError(
                f"unknown relationship definition fields: {names}."
            )
        payload = dict(data)
        try:
            if not isinstance(payload["relationship_type"], RelationshipType):
                payload["relationship_type"] = RelationshipType.from_dict(
                    payload["relationship_type"]
                )
            if not isinstance(payload["source"], RegistryReference):
                payload["source"] = RegistryReference.from_dict(payload["source"])
            if not isinstance(payload["target"], RegistryReference):
                payload["target"] = RegistryReference.from_dict(payload["target"])
        except KeyError as exc:
            raise RelationshipDefinitionError(
                f"missing required relationship definition field: {exc.args[0]}."
            ) from exc
        return cls(**payload)


__all__ = ["RelationshipDefinition", "RelationshipDefinitionError"]
