"""
============================================================
Nexa Provider Platform
File: registries/core/identifier_definition.py
Layer: Master Registry Foundation
Milestone: M008.2 — Registry Identifier Model
============================================================

Purpose
-------
Defines the immutable IdentifierDefinition model used throughout
the Registry Foundation.

An IdentifierDefinition describes one identifier type owned by a
registry namespace. It establishes the identifier's stable
identity, registry and namespace ownership, canonical code,
human-readable name, lifecycle status, optional format hints,
length boundaries, case-sensitivity policy, definition version,
and extension metadata.

Examples of identifier definitions include:

- Birth certificate reference number
- National identity number
- Passport number
- Driver licence number
- Tax identification number
- SIM registration number
- Provider registration number
- Internal platform reference number

The model is consumed by later Registry Foundation components,
including:

- Numbering strategies
- Identifier references
- Identifier validators
- Identifier issuers
- Registry repositories
- Registry services
- Administrative and diagnostic interfaces

The model does not:

- Allocate or issue identifier values
- Generate sequence numbers
- Compile or execute regular expressions
- Persist itself
- Confirm identifier uniqueness
- Resolve external records
- Apply registry-specific issuance policy

Those responsibilities belong to separate Registry Foundation
components.

Design Principles
-----------------
Immutable definition
    IdentifierDefinition is frozen and cannot be changed in place.

Explicit ownership
    Every identifier definition belongs to one registry and one
    namespace through registry_id and namespace_id.

Lightweight schema responsibility
    Construction normalizes values and protects essential object
    invariants. Rich business and format validation remains
    delegated to a future Identifier Validator.

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


DEFAULT_IDENTIFIER_DEFINITION_VERSION: Final[int] = 1
DEFAULT_IDENTIFIER_CASE_SENSITIVE: Final[bool] = False


class IdentifierDefinitionError(ValueError):
    """
    Raised when an invalid IdentifierDefinition is created.
    """


@dataclass(frozen=True, slots=True)
class IdentifierDefinition:
    """
    Immutable definition of one identifier type.
    """

    identifier_id: str
    registry_id: str
    namespace_id: str
    identifier_code: str
    identifier_name: str
    status: RegistryStatus = RegistryStatus.DRAFT
    description: str = ""
    pattern: str | None = None
    prefix: str | None = None
    minimum_length: int | None = None
    maximum_length: int | None = None
    case_sensitive: bool = DEFAULT_IDENTIFIER_CASE_SENSITIVE
    version: int = DEFAULT_IDENTIFIER_DEFINITION_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "identifier_id",
            self._normalize_required_text(
                self.identifier_id,
                field_name="identifier_id",
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
            "namespace_id",
            self._normalize_required_text(
                self.namespace_id,
                field_name="namespace_id",
            ),
        )
        object.__setattr__(
            self,
            "identifier_code",
            self._normalize_required_text(
                self.identifier_code,
                field_name="identifier_code",
            ).upper(),
        )
        object.__setattr__(
            self,
            "identifier_name",
            self._normalize_required_text(
                self.identifier_name,
                field_name="identifier_name",
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
        object.__setattr__(
            self,
            "pattern",
            self._normalize_nullable_text(
                self.pattern,
                field_name="pattern",
            ),
        )
        object.__setattr__(
            self,
            "prefix",
            self._normalize_nullable_text(
                self.prefix,
                field_name="prefix",
            ),
        )
        object.__setattr__(
            self,
            "minimum_length",
            self._normalize_optional_positive_integer(
                self.minimum_length,
                field_name="minimum_length",
            ),
        )
        object.__setattr__(
            self,
            "maximum_length",
            self._normalize_optional_positive_integer(
                self.maximum_length,
                field_name="maximum_length",
            ),
        )

        if (
            self.minimum_length is not None
            and self.maximum_length is not None
            and self.minimum_length > self.maximum_length
        ):
            raise IdentifierDefinitionError(
                "minimum_length cannot exceed maximum_length."
            )

        if not isinstance(self.case_sensitive, bool):
            raise TypeError(
                "case_sensitive must be a Boolean value."
            )

        if isinstance(self.version, bool) or not isinstance(
            self.version,
            int,
        ):
            raise TypeError(
                "version must be an integer."
            )

        if self.version < DEFAULT_IDENTIFIER_DEFINITION_VERSION:
            raise IdentifierDefinitionError(
                "version must be greater than or equal to "
                f"{DEFAULT_IDENTIFIER_DEFINITION_VERSION}."
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
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be text."
            )

        normalized = value.strip()

        if not normalized:
            raise IdentifierDefinitionError(
                f"{field_name} cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_optional_text(
        value: object,
        *,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be text."
            )

        return value.strip()

    @staticmethod
    def _normalize_nullable_text(
        value: object,
        *,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be text or None."
            )

        normalized = value.strip()

        return normalized or None

    @staticmethod
    def _normalize_optional_positive_integer(
        value: object,
        *,
        field_name: str,
    ) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(
                f"{field_name} must be an integer or None."
            )

        if value < 1:
            raise IdentifierDefinitionError(
                f"{field_name} must be greater than zero."
            )

        return value

    @staticmethod
    def _normalize_status(
        value: object,
    ) -> RegistryStatus:
        if isinstance(value, RegistryStatus):
            return value

        try:
            return RegistryStatus(value)
        except (TypeError, ValueError) as exc:
            raise IdentifierDefinitionError(
                f"Unsupported identifier status {value!r}."
            ) from exc

    @staticmethod
    def _normalize_metadata(
        value: object,
    ) -> Mapping[str, object]:
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
                raise IdentifierDefinitionError(
                    "metadata keys cannot be empty."
                )

            normalized_metadata[normalized_key] = item

        return MappingProxyType(normalized_metadata)

    @property
    def active(self) -> bool:
        return self.status is RegistryStatus.ACTIVE

    @property
    def inactive(self) -> bool:
        return not self.active

    @property
    def identity(self) -> tuple[str, str]:
        return (
            self.identifier_id,
            self.identifier_code,
        )

    @property
    def ownership(self) -> tuple[str, str]:
        return (
            self.registry_id,
            self.namespace_id,
        )

    @property
    def qualified_code(self) -> str:
        return (
            f"{self.registry_id}:"
            f"{self.namespace_id}:"
            f"{self.identifier_code}"
        )

    @property
    def has_pattern(self) -> bool:
        return self.pattern is not None

    @property
    def has_prefix(self) -> bool:
        return self.prefix is not None

    @property
    def fixed_length(self) -> bool:
        return bool(
            self.minimum_length is not None
            and self.maximum_length is not None
            and self.minimum_length == self.maximum_length
        )

    @property
    def length_bounded(self) -> bool:
        return bool(
            self.minimum_length is not None
            or self.maximum_length is not None
        )

    @property
    def exact_length(self) -> int | None:
        if not self.fixed_length:
            return None

        return self.minimum_length

    def allows_length(
        self,
        length: int,
    ) -> bool:
        if isinstance(length, bool) or not isinstance(length, int):
            raise TypeError(
                "length must be an integer."
            )

        if length < 0:
            raise ValueError(
                "length cannot be negative."
            )

        if (
            self.minimum_length is not None
            and length < self.minimum_length
        ):
            return False

        if (
            self.maximum_length is not None
            and length > self.maximum_length
        ):
            return False

        return True

    def metadata_value(
        self,
        key: str,
        default: object = None,
    ) -> object:
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
        if not isinstance(key, str):
            raise TypeError(
                "key must be text."
            )

        normalized_key = key.strip()

        if not normalized_key:
            return False

        return normalized_key in self.metadata

    def to_dict(self) -> dict[str, object]:
        return {
            "identifier_id": self.identifier_id,
            "registry_id": self.registry_id,
            "namespace_id": self.namespace_id,
            "identifier_code": self.identifier_code,
            "identifier_name": self.identifier_name,
            "status": self.status.value,
            "description": self.description,
            "pattern": self.pattern,
            "prefix": self.prefix,
            "minimum_length": self.minimum_length,
            "maximum_length": self.maximum_length,
            "case_sensitive": self.case_sensitive,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        values: Mapping[str, object],
    ) -> "IdentifierDefinition":
        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        return cls(**dict(values))

    def summary(self) -> str:
        length_description = "Unbounded"

        if self.fixed_length:
            length_description = str(self.exact_length)
        elif self.length_bounded:
            minimum = (
                str(self.minimum_length)
                if self.minimum_length is not None
                else "None"
            )
            maximum = (
                str(self.maximum_length)
                if self.maximum_length is not None
                else "None"
            )
            length_description = f"{minimum}..{maximum}"

        return (
            "========================================================\n"
            "Nexa Provider Platform\n"
            "Identifier Definition\n"
            "--------------------------------------------------------\n"
            f"Identifier ID : {self.identifier_id}\n"
            f"Registry ID   : {self.registry_id}\n"
            f"Namespace ID  : {self.namespace_id}\n"
            f"Code          : {self.identifier_code}\n"
            f"Name          : {self.identifier_name}\n"
            f"Status        : {self.status.value}\n"
            f"Length        : {length_description}\n"
            f"Version       : {self.version}\n"
            "========================================================"
        )


__all__ = (
    "DEFAULT_IDENTIFIER_CASE_SENSITIVE",
    "DEFAULT_IDENTIFIER_DEFINITION_VERSION",
    "IdentifierDefinition",
    "IdentifierDefinitionError",
)
