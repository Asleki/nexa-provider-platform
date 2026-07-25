"""
============================================================
Nexa Provider Platform
File: registries/ports/base_registry_repository.py
Layer: Master Registry Foundation
Milestone: NPP-M008.4 — Registry Repository Interface
============================================================

Abstract base for concrete registry repositories.

Provides only immutable repository metadata and common boundary
validation. It contains no collection, persistence, locking, adapter,
event, audit, lifecycle, or policy implementation.
============================================================
"""

from __future__ import annotations

from abc import ABC

from registries.core.base_registry import BaseRegistry

from .registry_repository import RegistryRepositoryInterface
from .registry_repository_errors import (
    RegistryIdentifierError,
    RegistryInvalidRecordError,
    RegistryRepositoryConfigurationError,
)


class BaseRegistryRepository(RegistryRepositoryInterface, ABC):
    """Shared boundary validation for registry repository adapters."""

    def __init__(
        self,
        repository_name: str,
        repository_type: str,
    ) -> None:
        if not isinstance(repository_name, str):
            raise RegistryRepositoryConfigurationError(
                "repository_name must be text."
            )
        normalized_name = repository_name.strip()
        if not normalized_name:
            raise RegistryRepositoryConfigurationError(
                "repository_name must not be empty."
            )

        if not isinstance(repository_type, str):
            raise RegistryRepositoryConfigurationError(
                "repository_type must be text."
            )
        normalized_type = repository_type.strip().lower()
        if not normalized_type:
            raise RegistryRepositoryConfigurationError(
                "repository_type must not be empty."
            )

        self._repository_name = normalized_name
        self._repository_type = normalized_type

    @property
    def repository_name(self) -> str:
        return self._repository_name

    @property
    def repository_type(self) -> str:
        return self._repository_type

    def validate_registry_id(self, registry_id: object) -> str:
        if not isinstance(registry_id, str):
            raise RegistryIdentifierError(
                "registry_id must be text.",
                repository=self.repository_name,
                repository_type=self.repository_type,
            )
        normalized = registry_id.strip()
        if not normalized:
            raise RegistryIdentifierError(
                "registry_id must not be empty.",
                repository=self.repository_name,
                repository_type=self.repository_type,
            )
        return normalized

    def validate_registry(
        self,
        registry: object,
    ) -> BaseRegistry:
        if not isinstance(registry, BaseRegistry):
            raise RegistryInvalidRecordError(
                "registry must be a BaseRegistry.",
                repository=self.repository_name,
                repository_type=self.repository_type,
            )
        self.validate_registry_id(registry.registry_id)
        return registry


__all__ = ["BaseRegistryRepository"]
