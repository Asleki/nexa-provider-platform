"""
============================================================
Nexa Provider Platform
File: registries/factories/registry_repository_factory.py
Layer: Master Registry Foundation
Milestone: NPP-M008.6 — Registry Factory
============================================================

Constructs approved registry repository adapters while keeping callers
independent from concrete persistence implementations.
============================================================
"""

from __future__ import annotations

from typing import Any

from registries.adapters.memory.memory_registry_repository import (
    MemoryRegistryRepository,
)
from registries.ports.registry_repository import RegistryRepositoryInterface

from .registry_repository_factory_errors import (
    RegistryRepositoryConstructionError,
    RegistryRepositoryFactoryConfigurationError,
)
from .registry_repository_registry import (
    RegistryRepositoryRegistry,
    normalize_registry_repository_type,
)

DEFAULT_REGISTRY_REPOSITORY_TYPE = "memory"


class RegistryRepositoryFactory:
    """Create registry repositories through an approved implementation registry."""

    def __init__(
        self,
        registry: RegistryRepositoryRegistry | None = None,
        *,
        register_defaults: bool = True,
    ) -> None:
        if registry is not None and not isinstance(
            registry, RegistryRepositoryRegistry
        ):
            raise RegistryRepositoryFactoryConfigurationError(
                "registry must be a RegistryRepositoryRegistry instance.",
                metadata={"actual_type": type(registry).__name__},
            )
        if not isinstance(register_defaults, bool):
            raise RegistryRepositoryFactoryConfigurationError(
                "register_defaults must be a boolean.",
                metadata={"actual_type": type(register_defaults).__name__},
            )

        self._registry = registry or RegistryRepositoryRegistry()
        if register_defaults:
            self.register_defaults()

    @property
    def registry(self) -> RegistryRepositoryRegistry:
        return self._registry

    def register_defaults(self) -> None:
        """Register built-in implementations without replacing injected choices."""

        if not self._registry.is_registered(DEFAULT_REGISTRY_REPOSITORY_TYPE):
            self._registry.register(
                DEFAULT_REGISTRY_REPOSITORY_TYPE,
                MemoryRegistryRepository,
            )

    def create(
        self,
        repository_type: str = DEFAULT_REGISTRY_REPOSITORY_TYPE,
        *args: Any,
        **kwargs: Any,
    ) -> RegistryRepositoryInterface:
        type_name = normalize_registry_repository_type(repository_type)
        repository_class = self._registry.get(type_name)

        try:
            repository = repository_class(*args, **kwargs)
        except Exception as exc:
            raise RegistryRepositoryConstructionError(
                "Unable to create registry-repository instance.",
                repository_type=type_name,
                cause=exc,
                metadata={"repository_class": repository_class.__name__},
            ) from exc

        if not isinstance(repository, RegistryRepositoryInterface):
            raise RegistryRepositoryConstructionError(
                "Created repository does not implement RegistryRepositoryInterface.",
                repository_type=type_name,
                metadata={
                    "repository_class": repository_class.__name__,
                    "actual_type": type(repository).__name__,
                },
            )
        return repository

    def create_memory(
        self,
        repository_name: str = "memory_registry_repository",
    ) -> MemoryRegistryRepository:
        repository = self.create(
            DEFAULT_REGISTRY_REPOSITORY_TYPE,
            repository_name=repository_name,
        )
        if not isinstance(repository, MemoryRegistryRepository):
            raise RegistryRepositoryConstructionError(
                "Registered memory repository is not MemoryRegistryRepository.",
                repository_type=DEFAULT_REGISTRY_REPOSITORY_TYPE,
                metadata={"actual_type": type(repository).__name__},
            )
        return repository


__all__ = [
    "DEFAULT_REGISTRY_REPOSITORY_TYPE",
    "RegistryRepositoryFactory",
]
