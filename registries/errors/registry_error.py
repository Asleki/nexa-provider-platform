"""
============================================================
Nexa Provider Platform
File: registries/errors/registry_error.py
Layer: Registry Error Foundation
Milestone: NPP-M006.2 — Registry Foundation
============================================================

Purpose
-------
Defines the common exception hierarchy used by Registry
Foundation components.

These exceptions represent domain and application failures
without coupling the registry layer to storage engines, HTTP
frameworks, logging systems, or external providers.

Design Principles
-----------------
Stable hierarchy
    All Registry Foundation exceptions inherit from RegistryError.

Structured context
    Errors may carry a stable machine-readable code, optional
    field name, optional resource reference, and immutable context.

Human-readable output
    The exception message remains clear when raised directly.

Storage independence
    No repository, database, transport, or runtime dependency.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final


DEFAULT_REGISTRY_ERROR_CODE: Final[str] = "REGISTRY_ERROR"


class RegistryError(Exception):
    """
    Base exception for all Registry Foundation failures.

    Parameters
    ----------
    message:
        Human-readable explanation of the failure.

    code:
        Stable machine-readable error code.

    field:
        Optional field associated with the failure.

    resource_reference:
        Optional stable registry, namespace, identifier, strategy,
        reference, subject, or relationship reference.

    context:
        Optional immutable diagnostic context.
    """

    __slots__ = (
        "message",
        "code",
        "field",
        "resource_reference",
        "context",
    )

    def __init__(
        self,
        message: str,
        *,
        code: str = DEFAULT_REGISTRY_ERROR_CODE,
        field: str | None = None,
        resource_reference: str | None = None,
        context: Mapping[str, object] | None = None,
    ) -> None:
        self.message = self._normalize_required_text(
            message,
            field_name="message",
        )
        self.code = self._normalize_required_text(
            code,
            field_name="code",
        ).upper()
        self.field = self._normalize_nullable_text(
            field,
            field_name="field",
        )
        self.resource_reference = self._normalize_nullable_text(
            resource_reference,
            field_name="resource_reference",
        )
        self.context = self._normalize_context(context)

        super().__init__(self.message)

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
            raise ValueError(
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
    def _normalize_context(
        value: Mapping[str, object] | None,
    ) -> Mapping[str, object]:
        if value is None:
            return MappingProxyType({})

        if not isinstance(value, Mapping):
            raise TypeError(
                "context must be a mapping or None."
            )

        normalized_context: dict[str, object] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    "context keys must be text."
                )

            normalized_key = key.strip()

            if not normalized_key:
                raise ValueError(
                    "context keys cannot be empty."
                )

            normalized_context[normalized_key] = item

        return MappingProxyType(normalized_context)

    @property
    def has_field(self) -> bool:
        return self.field is not None

    @property
    def has_resource_reference(self) -> bool:
        return self.resource_reference is not None

    @property
    def has_context(self) -> bool:
        return bool(self.context)

    def context_value(
        self,
        key: str,
        default: object = None,
    ) -> object:
        normalized_key = self._normalize_required_text(
            key,
            field_name="key",
        )

        return self.context.get(
            normalized_key,
            default,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "code": self.code,
            "field": self.field,
            "resource_reference": self.resource_reference,
            "context": dict(self.context),
        }

    def __str__(self) -> str:
        details: list[str] = [self.message]

        if self.field is not None:
            details.append(f"field={self.field}")

        if self.resource_reference is not None:
            details.append(
                f"resource={self.resource_reference}"
            )

        details.append(f"code={self.code}")

        return " | ".join(details)


class RegistryConfigurationError(RegistryError):
    """
    Raised when registry configuration is missing, inconsistent,
    unsupported, or cannot be safely applied.
    """


class RegistryValidationError(RegistryError):
    """
    Raised when validation failures prevent an operation from
    continuing.
    """


class RegistryNotFoundError(RegistryError):
    """
    Raised when a requested registry resource cannot be found.
    """


class RegistryConflictError(RegistryError):
    """
    Raised when an operation conflicts with existing registry
    state, identity, ownership, or uniqueness constraints.
    """


class RegistryStateError(RegistryError):
    """
    Raised when an operation is invalid for the current lifecycle
    state of a registry resource.
    """


class RegistryPermissionError(RegistryError):
    """
    Raised when an actor is not permitted to perform a registry
    operation.
    """


class RegistryIntegrityError(RegistryError):
    """
    Raised when registry data or relationships violate required
    integrity guarantees.
    """


class RegistryOperationError(RegistryError):
    """
    Raised when a registry operation cannot be completed for a
    domain-level reason not covered by a more specific exception.
    """


__all__ = (
    "DEFAULT_REGISTRY_ERROR_CODE",
    "RegistryError",
    "RegistryConfigurationError",
    "RegistryValidationError",
    "RegistryNotFoundError",
    "RegistryConflictError",
    "RegistryStateError",
    "RegistryPermissionError",
    "RegistryIntegrityError",
    "RegistryOperationError",
)
