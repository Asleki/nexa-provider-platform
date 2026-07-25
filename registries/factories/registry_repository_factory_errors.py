"""
============================================================
Nexa Provider Platform
File: registries/factories/registry_repository_factory_errors.py
Layer: Master Registry Foundation
Milestone: NPP-M008.6 — Registry Factory
============================================================

Factory-specific errors for registry repository registration and
construction. These errors extend the M008.4 repository error family
so callers retain one diagnostic shape across ports, adapters, and
factory boundaries.
============================================================
"""

from __future__ import annotations

from registries.ports.registry_repository_errors import RegistryRepositoryError


class RegistryRepositoryFactoryConfigurationError(
    RegistryRepositoryError,
    ValueError,
):
    """Raised when factory or implementation-registry configuration is invalid."""

    error_code = "NPP-REGISTRY-REPOSITORY-FACTORY-001"


class RegistryRepositoryRegistrationError(RegistryRepositoryError):
    """Base error for repository implementation registration failures."""

    error_code = "NPP-REGISTRY-REPOSITORY-FACTORY-010"


class RegistryRepositoryAlreadyRegisteredError(
    RegistryRepositoryRegistrationError,
    ValueError,
):
    """Raised when a repository type is registered without explicit replacement."""

    error_code = "NPP-REGISTRY-REPOSITORY-FACTORY-011"


class RegistryRepositoryNotRegisteredError(
    RegistryRepositoryRegistrationError,
    LookupError,
):
    """Raised when a requested repository type has no implementation."""

    error_code = "NPP-REGISTRY-REPOSITORY-FACTORY-012"


class RegistryRepositoryConstructionError(RegistryRepositoryError):
    """Raised when a registered repository implementation cannot be constructed."""

    error_code = "NPP-REGISTRY-REPOSITORY-FACTORY-020"


__all__ = [
    "RegistryRepositoryAlreadyRegisteredError",
    "RegistryRepositoryConstructionError",
    "RegistryRepositoryFactoryConfigurationError",
    "RegistryRepositoryNotRegisteredError",
    "RegistryRepositoryRegistrationError",
]
