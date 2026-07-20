"""
============================================================
Nexa Provider Platform
File: registries/errors/namespace_error.py
Layer: Registry Error Foundation
============================================================
"""

from __future__ import annotations

from .registry_error import (
    RegistryConflictError,
    RegistryNotFoundError,
    RegistryOperationError,
    RegistryStateError,
    RegistryValidationError,
)


class NamespaceError(RegistryOperationError):
    """Base exception for namespace-related failures."""


class NamespaceValidationError(RegistryValidationError, NamespaceError):
    """Raised when namespace validation fails."""


class NamespaceNotFoundError(RegistryNotFoundError, NamespaceError):
    """Raised when a namespace cannot be located."""


class NamespaceAlreadyExistsError(RegistryConflictError, NamespaceError):
    """Raised when a namespace already exists."""


class NamespaceCodeConflictError(NamespaceAlreadyExistsError):
    """Raised when a namespace code is already assigned."""


class NamespaceNameConflictError(NamespaceAlreadyExistsError):
    """Raised when a namespace name is already assigned."""


class NamespaceStateError(RegistryStateError, NamespaceError):
    """Raised when an operation is invalid for the namespace state."""


class NamespaceInactiveError(NamespaceStateError):
    """Raised when an operation requires an active namespace."""


class NamespaceArchivedError(NamespaceStateError):
    """Raised when an archived namespace is modified."""


class NamespaceReservedError(NamespaceStateError):
    """Raised when a reserved namespace cannot perform the requested operation."""


__all__ = (
    "NamespaceError",
    "NamespaceValidationError",
    "NamespaceNotFoundError",
    "NamespaceAlreadyExistsError",
    "NamespaceCodeConflictError",
    "NamespaceNameConflictError",
    "NamespaceStateError",
    "NamespaceInactiveError",
    "NamespaceArchivedError",
    "NamespaceReservedError",
)
