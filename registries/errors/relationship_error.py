"""
============================================================
Nexa Provider Platform
File: registries/errors/relationship_error.py
Layer: Registry Error Foundation
============================================================

Purpose
-------
Defines relationship-specific exceptions for Registry Foundation
operations.

These exceptions describe failures involving links between
registries, namespaces, identifiers, owners, providers, subjects,
or other registry resources without depending on relationship
storage or implementation details.

Dependency Direction
--------------------
This module depends only on the shared Registry Error Foundation.
It does not depend on relationship models, validators, adapters,
ports, governance, storage engines, or external frameworks.
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


class RelationshipError(RegistryOperationError):
    """Base exception for registry relationship failures."""


class RelationshipValidationError(
    RegistryValidationError,
    RelationshipError,
):
    """Raised when relationship data or structure fails validation."""


class RelationshipNotFoundError(
    RegistryNotFoundError,
    RelationshipError,
):
    """Raised when a requested relationship cannot be located."""


class RelationshipConflictError(
    RegistryConflictError,
    RelationshipError,
):
    """Raised when a relationship conflicts with existing state."""


class RelationshipAlreadyExistsError(RelationshipConflictError):
    """Raised when the same relationship has already been registered."""


class RelationshipDuplicateError(RelationshipAlreadyExistsError):
    """Raised when a duplicate relationship declaration is detected."""


class RelationshipCardinalityError(RelationshipConflictError):
    """Raised when a relationship exceeds an allowed cardinality."""


class RelationshipStateError(
    RegistryStateError,
    RelationshipError,
):
    """Raised when an operation is invalid for the relationship state."""


class RelationshipInactiveError(RelationshipStateError):
    """Raised when an operation requires an active relationship."""


class RelationshipSuspendedError(RelationshipStateError):
    """Raised when a suspended relationship cannot be used."""


class RelationshipRevokedError(RelationshipStateError):
    """Raised when a revoked relationship is used or modified."""


class RelationshipExpiredError(RelationshipStateError):
    """Raised when an expired relationship is used as active."""


class RelationshipImmutableError(RelationshipStateError):
    """Raised when an immutable relationship attribute is changed."""


class RelationshipIntegrityError(
    RegistryIntegrityError,
    RelationshipError,
):
    """Raised when relationship integrity guarantees are violated."""


class RelationshipEndpointError(RelationshipIntegrityError):
    """Raised when a relationship endpoint is invalid or unavailable."""


class RelationshipSourceNotFoundError(RelationshipEndpointError):
    """Raised when the relationship source cannot be resolved."""


class RelationshipTargetNotFoundError(RelationshipEndpointError):
    """Raised when the relationship target cannot be resolved."""


class RelationshipTypeMismatchError(RelationshipIntegrityError):
    """Raised when endpoints do not satisfy the relationship type."""


class RelationshipDirectionError(RelationshipIntegrityError):
    """Raised when relationship direction violates its definition."""


class RelationshipSelfReferenceError(RelationshipIntegrityError):
    """Raised when a prohibited self-referencing relationship is created."""


class RelationshipCycleError(RelationshipIntegrityError):
    """Raised when a prohibited relationship cycle is detected."""


class RelationshipRegistryMismatchError(RelationshipIntegrityError):
    """Raised when endpoints belong to incompatible registries."""


class RelationshipNamespaceMismatchError(RelationshipIntegrityError):
    """Raised when endpoints belong to incompatible namespaces."""


__all__ = (
    "RelationshipError",
    "RelationshipValidationError",
    "RelationshipNotFoundError",
    "RelationshipConflictError",
    "RelationshipAlreadyExistsError",
    "RelationshipDuplicateError",
    "RelationshipCardinalityError",
    "RelationshipStateError",
    "RelationshipInactiveError",
    "RelationshipSuspendedError",
    "RelationshipRevokedError",
    "RelationshipExpiredError",
    "RelationshipImmutableError",
    "RelationshipIntegrityError",
    "RelationshipEndpointError",
    "RelationshipSourceNotFoundError",
    "RelationshipTargetNotFoundError",
    "RelationshipTypeMismatchError",
    "RelationshipDirectionError",
    "RelationshipSelfReferenceError",
    "RelationshipCycleError",
    "RelationshipRegistryMismatchError",
    "RelationshipNamespaceMismatchError",
)
