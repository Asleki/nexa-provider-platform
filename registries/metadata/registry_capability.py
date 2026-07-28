"""Immutable declaration of one capability supported by a registry.

A capability declares *what* a registry recognises.  It does not grant
permission, perform the operation, or define the payload used by a future
domain implementation.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from .registry_capability_category import RegistryCapabilityCategory
from .registry_metadata_errors import RegistryCapabilityError

_CAPABILITY_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
)
_CAPABILITY_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$"
)
_MAX_CAPABILITY_CODE_LENGTH: Final[int] = 255
_MAX_CAPABILITY_NAME_LENGTH: Final[int] = 200
_MAX_DESCRIPTION_LENGTH: Final[int] = 2_000


def _freeze_attribute_value(value: object) -> object:
    """Return an immutable snapshot of a nested attribute value."""
    if isinstance(value, Mapping):
        frozen: dict[object, object] = {}
        for key, nested_value in value.items():
            try:
                hash(key)
            except TypeError as exc:
                raise TypeError("attribute mapping keys must be hashable.") from exc
            frozen[key] = _freeze_attribute_value(nested_value)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_attribute_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_attribute_value(item) for item in value)
    return value


def _thaw_attribute_value(value: object) -> object:
    """Return a detached serialisable-style copy of an attribute value."""
    if isinstance(value, Mapping):
        return {key: _thaw_attribute_value(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_attribute_value(item) for item in value]
    if isinstance(value, frozenset):
        return [
            _thaw_attribute_value(item)
            for item in sorted(value, key=lambda item: repr(item))
        ]
    return value


@dataclass(frozen=True, slots=True)
class RegistryCapability:
    """One stable, versioned and runtime-aware registry capability."""

    capability_id: str
    capability_code: str
    capability_name: str
    category: RegistryCapabilityCategory
    description: str = ""
    supported: bool = True
    simulation_supported: bool = True
    production_supported: bool = False
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        capability_id = self._normalise_required_text("capability_id", self.capability_id)
        if not _CAPABILITY_ID_PATTERN.fullmatch(capability_id):
            raise RegistryCapabilityError(
                "capability_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "capability_id", capability_id)

        capability_code = self._normalise_required_text(
            "capability_code", self.capability_code
        ).upper()
        if len(capability_code) > _MAX_CAPABILITY_CODE_LENGTH:
            raise RegistryCapabilityError(
                f"capability_code cannot exceed {_MAX_CAPABILITY_CODE_LENGTH} characters."
            )
        if not _CAPABILITY_CODE_PATTERN.fullmatch(capability_code):
            raise RegistryCapabilityError(
                "capability_code must be a hierarchical dotted code with at least "
                "two uppercase semantic segments."
            )
        object.__setattr__(self, "capability_code", capability_code)

        capability_name = self._normalise_required_text(
            "capability_name", self.capability_name
        )
        if len(capability_name) > _MAX_CAPABILITY_NAME_LENGTH:
            raise RegistryCapabilityError(
                f"capability_name cannot exceed {_MAX_CAPABILITY_NAME_LENGTH} characters."
            )
        object.__setattr__(self, "capability_name", capability_name)

        if not isinstance(self.description, str):
            raise TypeError("description must be text.")
        description = self.description.strip()
        if len(description) > _MAX_DESCRIPTION_LENGTH:
            raise RegistryCapabilityError(
                f"description cannot exceed {_MAX_DESCRIPTION_LENGTH} characters."
            )
        object.__setattr__(self, "description", description)

        try:
            category = RegistryCapabilityCategory.from_value(self.category)
        except ValueError as exc:
            raise RegistryCapabilityError(str(exc)) from exc
        object.__setattr__(self, "category", category)

        for name in ("supported", "simulation_supported", "production_supported"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")

        if self.production_supported and not self.supported:
            raise RegistryCapabilityError(
                "production_supported requires supported=True."
            )
        if self.simulation_supported and not self.supported:
            raise RegistryCapabilityError(
                "simulation_supported requires supported=True."
            )

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RegistryCapabilityError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        for key in self.attributes:
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            if not key.strip():
                raise RegistryCapabilityError("attribute keys cannot be empty.")
        frozen_attributes = {
            key.strip(): _freeze_attribute_value(value)
            for key, value in self.attributes.items()
        }
        if len(frozen_attributes) != len(self.attributes):
            raise RegistryCapabilityError(
                "attribute keys must remain unique after whitespace normalization."
            )
        object.__setattr__(self, "attributes", MappingProxyType(frozen_attributes))

    @staticmethod
    def _normalise_required_text(name: str, value: object) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{name} must be text.")
        normalized = value.strip()
        if not normalized:
            raise RegistryCapabilityError(f"{name} cannot be empty.")
        return normalized

    def to_dict(self) -> dict[str, object]:
        """Return a detached representation suitable for persistence or transport."""
        return {
            "capability_id": self.capability_id,
            "capability_code": self.capability_code,
            "capability_name": self.capability_name,
            "category": self.category.value,
            "description": self.description,
            "supported": self.supported,
            "simulation_supported": self.simulation_supported,
            "production_supported": self.production_supported,
            "version": self.version,
            "attributes": _thaw_attribute_value(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RegistryCapability":
        """Build a capability from a mapping without retaining caller ownership."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        return cls(**dict(data))


__all__ = ["RegistryCapability"]
