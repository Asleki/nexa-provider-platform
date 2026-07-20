"""
============================================================
Nexa Provider Platform
File: registries/errors/identifier_error.py
Layer: Registry Error Foundation
============================================================

Purpose
-------
Defines identifier-specific exceptions used by Registry
Foundation services, validators, governance rules, catalogues,
relationships, ports, and adapters.

Dependency Direction
--------------------
This module depends only on the shared Registry Error Foundation.
It does not depend on validators, adapters, ports, governance,
relationships, storage engines, or external frameworks.
============================================================
"""

from __future__ import annotations

from .registry_error import (
    RegistryConflictError,
    RegistryIntegrityError,
    RegistryNotFoundError,
    RegistryOperationError,
    RegistryStateError,
    RegistryValidationError,
)


class IdentifierError(RegistryOperationError):
    """Base exception for identifier-related failures."""


class IdentifierValidationError(RegistryValidationError, IdentifierError):
    """Raised when identifier data or structure fails validation."""


class IdentifierNotFoundError(RegistryNotFoundError, IdentifierError):
    """Raised when an identifier cannot be located."""


class IdentifierConflictError(RegistryConflictError, IdentifierError):
    """Raised when an identifier conflicts with existing registry state."""


class IdentifierAlreadyExistsError(IdentifierConflictError):
    """Raised when the same identifier has already been registered."""


class IdentifierValueConflictError(IdentifierConflictError):
    """Raised when an identifier value is already assigned."""


class IdentifierReferenceConflictError(IdentifierConflictError):
    """Raised when an identifier reference conflicts with another record."""


class IdentifierStateError(RegistryStateError, IdentifierError):
    """Raised when an operation is invalid for the identifier lifecycle state."""


class IdentifierInactiveError(IdentifierStateError):
    """Raised when an operation requires an active identifier."""


class IdentifierSuspendedError(IdentifierStateError):
    """Raised when a suspended identifier cannot perform an operation."""


class IdentifierRevokedError(IdentifierStateError):
    """Raised when a revoked identifier is used or modified."""


class IdentifierExpiredError(IdentifierStateError):
    """Raised when an expired identifier is used for an active operation."""


class IdentifierRetiredError(IdentifierStateError):
    """Raised when a retired identifier is used or modified."""


class IdentifierImmutableError(IdentifierStateError):
    """Raised when an immutable identifier field is changed."""


class IdentifierIntegrityError(RegistryIntegrityError, IdentifierError):
    """Raised when identifier integrity guarantees are violated."""


class IdentifierNamespaceMismatchError(IdentifierIntegrityError):
    """Raised when an identifier does not belong to the expected namespace."""


class IdentifierRegistryMismatchError(IdentifierIntegrityError):
    """Raised when an identifier does not belong to the expected registry."""


class IdentifierDefinitionMismatchError(IdentifierIntegrityError):
    """Raised when an identifier violates its identifier definition."""


class IdentifierLifecycleMismatchError(IdentifierIntegrityError):
    """Raised when identifier state conflicts with its lifecycle history."""


__all__ = (
    "IdentifierError",
    "IdentifierValidationError",
    "IdentifierNotFoundError",
    "IdentifierConflictError",
    "IdentifierAlreadyExistsError",
    "IdentifierValueConflictError",
    "IdentifierReferenceConflictError",
    "IdentifierStateError",
    "IdentifierInactiveError",
    "IdentifierSuspendedError",
    "IdentifierRevokedError",
    "IdentifierExpiredError",
    "IdentifierRetiredError",
    "IdentifierImmutableError",
    "IdentifierIntegrityError",
    "IdentifierNamespaceMismatchError",
    "IdentifierRegistryMismatchError",
    "IdentifierDefinitionMismatchError",
    "IdentifierLifecycleMismatchError",
)
