"""
============================================================
Nexa Provider Platform
File: registries/core/registry_definition.py
Layer: Master Registry Foundation
Milestone: NPP-M008.1 — Registry Contracts
============================================================

Purpose
-------
Defines the immutable RegistryDefinition model that concretely
satisfies the M008.1 registry-definition contract.

A RegistryDefinition describes one registry as a platform
resource. It establishes the registry's stable identity,
human-readable name, family classification, lifecycle status,
definition version, optional description, and extension metadata.

The model is consumed by later Registry Foundation components,
including:

- Namespace definitions
- Identifier definitions
- Numbering strategies
- Identifier references
- Registry validators
- Registry repositories
- Registry services
- Administrative and diagnostic interfaces

The model does not:

- Store operational registry records
- Allocate or issue identifiers
- Persist itself
- Read configuration sources
- Connect to storage systems
- Perform cross-registry validation
- Apply business-specific registry policy

Those responsibilities belong to separate Registry Foundation
components.

Design Principles
-----------------
Immutable definition
    RegistryDefinition is frozen and cannot be changed in place.

Lightweight schema responsibility
    Construction performs normalization and protects essential
    object invariants. Rich business and cross-field validation
    remains the responsibility of a dedicated registry validator.

Storage independence
    The model does not depend on files, JSON, SQL, Supabase, or
    any repository implementation.

Predictable conversion
    Explicit to_dict() and from_dict() methods provide stable
    application-boundary conversion.

Read-only metadata
    Metadata is defensively copied and exposed through an
    immutable mapping view.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from .registry_family import RegistryFamily
from .registry_status import RegistryStatus


"""
============================================================
SECTION 1 — Registry Definition Constants
============================================================

DEFAULT_REGISTRY_DEFINITION_VERSION
    Version assigned when no explicit definition version is
    supplied.

The RegistryDefinition model intentionally defines only the
minimum construction constant required by the schema. Detailed
limits and policy rules belong in the future Registry Validator.
============================================================
"""

DEFAULT_REGISTRY_DEFINITION_VERSION: Final[int] = 1


"""
============================================================
SECTION 2 — Registry Definition Exception
============================================================
"""


class RegistryDefinitionError(ValueError):
    """
    Raised when an invalid RegistryDefinition is created.
    """


"""
============================================================
SECTION 3 — Registry Definition Model
============================================================
"""


@dataclass(frozen=True, slots=True)
class RegistryDefinition:
    """
    Immutable definition of one platform registry.

    Parameters
    ----------
    registry_id:
        Stable machine-facing identifier for the registry.

    registry_code:
        Short canonical code used by platform components.

    registry_name:
        Human-readable registry name.

    family:
        Registry-family classification.

    status:
        Registry lifecycle status.

    description:
        Optional human-readable registry description.

    version:
        Positive registry-definition version.

    metadata:
        Optional extension metadata. The mapping is copied and
        exposed as read-only.
    """

    registry_id: str

    registry_code: str

    registry_name: str

    family: RegistryFamily

    status: RegistryStatus = RegistryStatus.DRAFT

    description: str = ""

    version: int = DEFAULT_REGISTRY_DEFINITION_VERSION

    metadata: Mapping[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Normalize values and enforce essential invariants.

        Full business validation is intentionally delegated to a
        dedicated Registry Validator.
        """

        object.__setattr__(
            self,
            "registry_id",
            self._normalize_required_text(
                self.registry_id,
                field_name="registry_id",
            ),
        )

        object.__setattr__(
            self,
            "registry_code",
            self._normalize_required_text(
                self.registry_code,
                field_name="registry_code",
            ).upper(),
        )

        object.__setattr__(
            self,
            "registry_name",
            self._normalize_required_text(
                self.registry_name,
                field_name="registry_name",
            ),
        )

        object.__setattr__(
            self,
            "family",
            self._normalize_family(self.family),
        )

        object.__setattr__(
            self,
            "status",
            self._normalize_status(self.status),
        )

        object.__setattr__(
            self,
            "description",
            self._normalize_optional_text(
                self.description,
                field_name="description",
            ),
        )

        if isinstance(self.version, bool) or not isinstance(
            self.version,
            int,
        ):
            raise TypeError(
                "version must be an integer."
            )

        if self.version < DEFAULT_REGISTRY_DEFINITION_VERSION:
            raise RegistryDefinitionError(
                "version must be greater than or equal to "
                f"{DEFAULT_REGISTRY_DEFINITION_VERSION}."
            )

        object.__setattr__(
            self,
            "metadata",
            self._normalize_metadata(self.metadata),
        )

    @staticmethod
    def _normalize_required_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """
        Normalize one required text field.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be text."
            )

        normalized = value.strip()

        if not normalized:
            raise RegistryDefinitionError(
                f"{field_name} cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_optional_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """
        Normalize one optional text field.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be text."
            )

        return value.strip()

    @staticmethod
    def _normalize_family(
        value: object,
    ) -> RegistryFamily:
        """
        Normalize a registry-family value.
        """

        if isinstance(value, RegistryFamily):
            return value

        try:
            return RegistryFamily(value)
        except (TypeError, ValueError) as exc:
            raise RegistryDefinitionError(
                f"Unsupported registry family {value!r}."
            ) from exc

    @staticmethod
    def _normalize_status(
        value: object,
    ) -> RegistryStatus:
        """
        Normalize a registry-status value.
        """

        if isinstance(value, RegistryStatus):
            return value

        try:
            return RegistryStatus(value)
        except (TypeError, ValueError) as exc:
            raise RegistryDefinitionError(
                f"Unsupported registry status {value!r}."
            ) from exc

    @staticmethod
    def _normalize_metadata(
        value: object,
    ) -> Mapping[str, object]:
        """
        Defensively copy metadata into a read-only mapping.

        Detailed metadata content validation remains delegated to
        the future Registry Validator.
        """

        if not isinstance(value, Mapping):
            raise TypeError(
                "metadata must be a mapping."
            )

        normalized_metadata: dict[str, object] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    "metadata keys must be text."
                )

            normalized_key = key.strip()

            if not normalized_key:
                raise RegistryDefinitionError(
                    "metadata keys cannot be empty."
                )

            normalized_metadata[normalized_key] = item

        return MappingProxyType(normalized_metadata)

    """
    ============================================================
    SECTION 4 — Identity and Lifecycle Properties
    ============================================================
    """

    @property
    def active(self) -> bool:
        """
        Return True when the registry is active.
        """

        return self.status is RegistryStatus.ACTIVE

    @property
    def inactive(self) -> bool:
        """
        Return True when the registry is not active.
        """

        return not self.active

    @property
    def identity(self) -> tuple[str, str]:
        """
        Return the stable registry identity pair.
        """

        return (
            self.registry_id,
            self.registry_code,
        )

    @property
    def qualified_code(self) -> str:
        """
        Return a family-qualified registry code.
        """

        return (
            f"{self.family.value}:"
            f"{self.registry_code}"
        )

    """
    ============================================================
    SECTION 5 — Metadata Access
    ============================================================
    """

    def metadata_value(
        self,
        key: str,
        default: object = None,
    ) -> object:
        """
        Return one metadata value.

        The default value is returned when the key is absent.
        """

        if not isinstance(key, str):
            raise TypeError(
                "key must be text."
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                "key cannot be empty."
            )

        return self.metadata.get(
            normalized_key,
            default,
        )

    def has_metadata(
        self,
        key: str,
    ) -> bool:
        """
        Return True when a metadata key exists.
        """

        if not isinstance(key, str):
            raise TypeError(
                "key must be text."
            )

        normalized_key = key.strip()

        if not normalized_key:
            return False

        return normalized_key in self.metadata

    """
    ============================================================
    SECTION 6 — Serialization
    ============================================================
    """

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the registry definition.
        """

        return {
            "registry_id": self.registry_id,
            "registry_code": self.registry_code,
            "registry_name": self.registry_name,
            "family": self.family.value,
            "status": self.status.value,
            "description": self.description,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        values: Mapping[str, object],
    ) -> "RegistryDefinition":
        """
        Construct a RegistryDefinition from a mapping.

        Unknown fields are rejected by the dataclass constructor,
        preserving a strict and predictable public schema.
        """

        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        normalized_values = dict(values)

        return cls(**normalized_values)

    """
    ============================================================
    SECTION 7 — Human-Readable Representation
    ============================================================
    """

    def summary(self) -> str:
        """
        Return a human-readable registry-definition summary.
        """

        return (
            "========================================================\n"
            "Nexa Provider Platform\n"
            "Registry Definition\n"
            "--------------------------------------------------------\n"
            f"Registry ID : {self.registry_id}\n"
            f"Code        : {self.registry_code}\n"
            f"Name        : {self.registry_name}\n"
            f"Family      : {self.family.value}\n"
            f"Status      : {self.status.value}\n"
            f"Version     : {self.version}\n"
            "========================================================"
        )


"""
============================================================
SECTION 8 — Public Exports
============================================================
"""

__all__ = (
    "DEFAULT_REGISTRY_DEFINITION_VERSION",
    "RegistryDefinition",
    "RegistryDefinitionError",
)
