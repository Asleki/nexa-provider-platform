"""
============================================================
Nexa Provider Platform
File: registries/core/identifier_reference.py
Layer: Master Registry Foundation
Milestone: M008.2 — Registry Identifier Model
============================================================

Purpose
-------
Defines the immutable IdentifierReference value object used by
the Registry Foundation.

An IdentifierReference represents one concrete identifier value
associated with a subject. It links the value to its registry,
namespace, and identifier definition while remaining independent
of storage, allocation, verification, and external-provider logic.

Examples include references to:

- A birth certificate reference number
- A national identity number
- A passport number
- A SIM registration number
- A tax identification number
- A provider registration number
- An internal platform identifier

The model does not:

- Generate identifier values
- Confirm uniqueness
- Verify an identifier against an external authority
- Persist itself
- Resolve the referenced subject
- Apply identifier-format rules
- Mutate lifecycle state in place

Those responsibilities belong to validators, registries,
repositories, issuance services, and verification adapters.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from .identifier_lifecycle import IdentifierLifecycle


DEFAULT_IDENTIFIER_REFERENCE_VERSION: Final[int] = 1


class IdentifierReferenceError(ValueError):
    """
    Raised when an invalid IdentifierReference is created.
    """


@dataclass(frozen=True, slots=True)
class IdentifierReference:
    """
    Immutable reference to one concrete identifier value.

    Parameters
    ----------
    reference_id:
        Stable internal identity of this reference record.

    registry_id:
        Stable identifier of the owning registry.

    namespace_id:
        Stable identifier of the owning namespace.

    identifier_id:
        Stable identifier of the applicable identifier definition.

    subject_reference:
        Stable platform reference to the person, organisation,
        account, device, asset, or other subject that owns or uses
        the identifier.

    identifier_value:
        Concrete identifier value. Construction trims surrounding
        whitespace but does not apply definition-specific format
        validation.

    status:
        Lifecycle status of the identifier reference.

    source_reference:
        Optional reference to the source record, import batch,
        external system, or issuance event that supplied the value.

    version:
        Positive reference-model version.

    metadata:
        Optional extension metadata. The mapping is defensively
        copied and exposed as read-only.
    """

    reference_id: str
    registry_id: str
    namespace_id: str
    identifier_id: str
    subject_reference: str
    identifier_value: str
    status: IdentifierLifecycle = IdentifierLifecycle.REQUESTED
    source_reference: str | None = None
    version: int = DEFAULT_IDENTIFIER_REFERENCE_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "reference_id",
            "registry_id",
            "namespace_id",
            "identifier_id",
            "subject_reference",
            "identifier_value",
        ):
            object.__setattr__(
                self,
                field_name,
                self._normalize_required_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        object.__setattr__(
            self,
            "status",
            self._normalize_status(self.status),
        )

        object.__setattr__(
            self,
            "source_reference",
            self._normalize_nullable_text(
                self.source_reference,
                field_name="source_reference",
            ),
        )

        if isinstance(self.version, bool) or not isinstance(
            self.version,
            int,
        ):
            raise TypeError(
                "version must be an integer."
            )

        if self.version < DEFAULT_IDENTIFIER_REFERENCE_VERSION:
            raise IdentifierReferenceError(
                "version must be greater than or equal to "
                f"{DEFAULT_IDENTIFIER_REFERENCE_VERSION}."
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
            raise IdentifierReferenceError(
                f"{field_name} cannot be empty."
            )

        return normalized

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
    def _normalize_status(
        value: object,
    ) -> IdentifierLifecycle:
        if isinstance(value, IdentifierLifecycle):
            return value

        try:
            return IdentifierLifecycle(value)
        except (TypeError, ValueError) as exc:
            raise IdentifierReferenceError(
                f"Unsupported identifier-reference status {value!r}."
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
                raise IdentifierReferenceError(
                    "metadata keys cannot be empty."
                )

            normalized_metadata[normalized_key] = item

        return MappingProxyType(normalized_metadata)

    @property
    def active(self) -> bool:
        """
        Return True when the identifier reference is active.
        """

        return self.status is IdentifierLifecycle.ACTIVE

    @property
    def inactive(self) -> bool:
        """
        Return True when the identifier reference is not active.
        """

        return not self.active

    @property
    def identity(self) -> tuple[str, str]:
        """
        Return the stable reference identity and identifier value.
        """

        return (
            self.reference_id,
            self.identifier_value,
        )

    @property
    def ownership(self) -> tuple[str, str, str]:
        """
        Return registry, namespace, and identifier-definition IDs.
        """

        return (
            self.registry_id,
            self.namespace_id,
            self.identifier_id,
        )

    @property
    def qualified_reference(self) -> str:
        """
        Return a fully qualified identifier-reference string.
        """

        return (
            f"{self.registry_id}:"
            f"{self.namespace_id}:"
            f"{self.identifier_id}:"
            f"{self.identifier_value}"
        )

    @property
    def sourced(self) -> bool:
        """
        Return True when a source reference is available.
        """

        return self.source_reference is not None

    def metadata_value(
        self,
        key: str,
        default: object = None,
    ) -> object:
        """
        Return one metadata value or the supplied default.
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
        Return True when a normalized metadata key exists.
        """

        if not isinstance(key, str):
            raise TypeError(
                "key must be text."
            )

        normalized_key = key.strip()

        if not normalized_key:
            return False

        return normalized_key in self.metadata

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the identifier reference.
        """

        return {
            "reference_id": self.reference_id,
            "registry_id": self.registry_id,
            "namespace_id": self.namespace_id,
            "identifier_id": self.identifier_id,
            "subject_reference": self.subject_reference,
            "identifier_value": self.identifier_value,
            "status": self.status.value,
            "source_reference": self.source_reference,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        values: Mapping[str, object],
    ) -> "IdentifierReference":
        """
        Construct an IdentifierReference from a mapping.
        """

        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        return cls(**dict(values))

    def summary(self) -> str:
        """
        Return a human-readable identifier-reference summary.
        """

        source = self.source_reference or "None"

        return (
            "========================================================\n"
            "Nexa Provider Platform\n"
            "Identifier Reference\n"
            "--------------------------------------------------------\n"
            f"Reference ID      : {self.reference_id}\n"
            f"Registry ID       : {self.registry_id}\n"
            f"Namespace ID      : {self.namespace_id}\n"
            f"Identifier ID     : {self.identifier_id}\n"
            f"Subject Reference : {self.subject_reference}\n"
            f"Identifier Value  : {self.identifier_value}\n"
            f"Status            : {self.status.value}\n"
            f"Source Reference  : {source}\n"
            f"Version           : {self.version}\n"
            "========================================================"
        )


__all__ = (
    "DEFAULT_IDENTIFIER_REFERENCE_VERSION",
    "IdentifierReference",
    "IdentifierReferenceError",
)
