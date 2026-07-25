"""
============================================================
Nexa Provider Platform
File: registries/core/namespace_definition.py
Layer: Master Registry Foundation
Milestone: M008.2 — Registry Identifier Model
============================================================

Purpose
-------
Defines the immutable NamespaceDefinition model used throughout
the Registry Foundation.

A NamespaceDefinition describes one logical namespace owned by a
registry. It provides a stable boundary within which identifier
definitions and numbering strategies may later operate.

The model is consumed by later Registry Foundation components,
including:

- Identifier definitions
- Numbering strategies
- Identifier references
- Namespace validators
- Registry repositories
- Registry services
- Administrative and diagnostic interfaces

The model does not:

- Allocate identifiers
- Generate sequence values
- Persist itself
- Load registry records
- Resolve registry relationships
- Apply cross-namespace policy
- Validate identifier formats

Those responsibilities belong to separate Registry Foundation
components.

Design Principles
-----------------
Immutable definition
    NamespaceDefinition is frozen and cannot be changed in place.

Registry ownership
    Every namespace belongs to one registry through registry_id.

Lightweight schema responsibility
    Construction normalizes values and protects essential object
    invariants. Rich business validation remains delegated to a
    future namespace or registry validator.

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

from .registry_status import RegistryStatus


"""
============================================================
SECTION 1 — Namespace Definition Constants
============================================================
"""

DEFAULT_NAMESPACE_DEFINITION_VERSION: Final[int] = 1


"""
============================================================
SECTION 2 — Namespace Definition Exception
============================================================
"""


class NamespaceDefinitionError(ValueError):
    """
    Raised when an invalid NamespaceDefinition is created.
    """


"""
============================================================
SECTION 3 — Namespace Definition Model
============================================================
"""


@dataclass(frozen=True, slots=True)
class NamespaceDefinition:
    """
    Immutable definition of one registry namespace.

    Parameters
    ----------
    namespace_id:
        Stable machine-facing identifier for the namespace.

    registry_id:
        Stable identifier of the owning registry.

    namespace_code:
        Short canonical code used by platform components.

    namespace_name:
        Human-readable namespace name.

    status:
        Namespace lifecycle status.

    description:
        Optional human-readable namespace description.

    version:
        Positive namespace-definition version.

    metadata:
        Optional extension metadata. The mapping is copied and
        exposed as read-only.
    """

    namespace_id: str

    registry_id: str

    namespace_code: str

    namespace_name: str

    status: RegistryStatus = RegistryStatus.DRAFT

    description: str = ""

    version: int = DEFAULT_NAMESPACE_DEFINITION_VERSION

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
            "namespace_id",
            self._normalize_required_text(
                self.namespace_id,
                field_name="namespace_id",
            ),
        )

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
            "namespace_code",
            self._normalize_required_text(
                self.namespace_code,
                field_name="namespace_code",
            ).upper(),
        )

        object.__setattr__(
            self,
            "namespace_name",
            self._normalize_required_text(
                self.namespace_name,
                field_name="namespace_name",
            ),
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

        if self.version < DEFAULT_NAMESPACE_DEFINITION_VERSION:
            raise NamespaceDefinitionError(
                "version must be greater than or equal to "
                f"{DEFAULT_NAMESPACE_DEFINITION_VERSION}."
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
            raise NamespaceDefinitionError(
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
            raise NamespaceDefinitionError(
                f"Unsupported namespace status {value!r}."
            ) from exc

    @staticmethod
    def _normalize_metadata(
        value: object,
    ) -> Mapping[str, object]:
        """
        Defensively copy metadata into a read-only mapping.

        Detailed metadata-content validation remains delegated to
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
                raise NamespaceDefinitionError(
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
        Return True when the namespace is active.
        """

        return self.status is RegistryStatus.ACTIVE

    @property
    def inactive(self) -> bool:
        """
        Return True when the namespace is not active.
        """

        return not self.active

    @property
    def identity(self) -> tuple[str, str]:
        """
        Return the stable namespace identity pair.
        """

        return (
            self.namespace_id,
            self.namespace_code,
        )

    @property
    def registry_identity(self) -> tuple[str, str]:
        """
        Return the owning registry and namespace identifiers.
        """

        return (
            self.registry_id,
            self.namespace_id,
        )

    @property
    def qualified_code(self) -> str:
        """
        Return a registry-qualified namespace code.
        """

        return (
            f"{self.registry_id}:"
            f"{self.namespace_code}"
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
        Serialize the namespace definition.
        """

        return {
            "namespace_id": self.namespace_id,
            "registry_id": self.registry_id,
            "namespace_code": self.namespace_code,
            "namespace_name": self.namespace_name,
            "status": self.status.value,
            "description": self.description,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        values: Mapping[str, object],
    ) -> "NamespaceDefinition":
        """
        Construct a NamespaceDefinition from a mapping.

        Unknown fields are rejected by the dataclass constructor,
        preserving a strict and predictable public schema.
        """

        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        return cls(**dict(values))

    """
    ============================================================
    SECTION 7 — Human-Readable Representation
    ============================================================
    """

    def summary(self) -> str:
        """
        Return a human-readable namespace-definition summary.
        """

        return (
            "========================================================\n"
            "Nexa Provider Platform\n"
            "Namespace Definition\n"
            "--------------------------------------------------------\n"
            f"Namespace ID : {self.namespace_id}\n"
            f"Registry ID  : {self.registry_id}\n"
            f"Code         : {self.namespace_code}\n"
            f"Name         : {self.namespace_name}\n"
            f"Status       : {self.status.value}\n"
            f"Version      : {self.version}\n"
            "========================================================"
        )


"""
============================================================
SECTION 8 — Public Exports
============================================================
"""

__all__ = (
    "DEFAULT_NAMESPACE_DEFINITION_VERSION",
    "NamespaceDefinition",
    "NamespaceDefinitionError",
)
