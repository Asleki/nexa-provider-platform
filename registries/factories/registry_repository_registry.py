"""
============================================================
Nexa Provider Platform
File: registries/factories/registry_repository_registry.py
Layer: Master Registry Foundation
Milestone: NPP-M008.6 — Registry Factory
============================================================

Technical registry of concrete registry-repository implementation
classes. This is not the M008.7 domain Registry Catalogue.
============================================================
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypeAlias

from registries.ports.registry_repository import RegistryRepositoryInterface

from .registry_repository_factory_errors import (
    RegistryRepositoryAlreadyRegisteredError,
    RegistryRepositoryFactoryConfigurationError,
    RegistryRepositoryNotRegisteredError,
    RegistryRepositoryRegistrationError,
)

RegistryRepositoryClass: TypeAlias = type[RegistryRepositoryInterface]


def normalize_registry_repository_type(repository_type: object) -> str:
    """Normalize a repository implementation type to a stable lowercase key."""

    if not isinstance(repository_type, str):
        raise RegistryRepositoryFactoryConfigurationError(
            "repository_type must be text.",
            metadata={"actual_type": type(repository_type).__name__},
        )

    normalized = repository_type.strip().lower()
    if not normalized:
        raise RegistryRepositoryFactoryConfigurationError(
            "repository_type must not be empty."
        )
    return normalized


class RegistryRepositoryRegistry:
    """Store approved registry-repository implementation classes by type."""

    def __init__(self) -> None:
        self._repositories: dict[str, RegistryRepositoryClass] = {}

    def register(
        self,
        repository_type: str,
        repository_class: RegistryRepositoryClass,
        *,
        replace: bool = False,
    ) -> None:
        type_name = normalize_registry_repository_type(repository_type)

        if not isinstance(repository_class, type):
            raise RegistryRepositoryFactoryConfigurationError(
                "repository_class must be a class.",
                repository_type=type_name,
                metadata={"actual_type": type(repository_class).__name__},
            )
        if not issubclass(repository_class, RegistryRepositoryInterface):
            raise RegistryRepositoryFactoryConfigurationError(
                "repository_class must implement RegistryRepositoryInterface.",
                repository_type=type_name,
                metadata={"repository_class": repository_class.__name__},
            )
        if type_name in self._repositories and not replace:
            raise RegistryRepositoryAlreadyRegisteredError(
                f"Registry repository type is already registered: {type_name}",
                repository_type=type_name,
                metadata={
                    "repository_class": self._repositories[type_name].__name__
                },
            )
        try:
            self._repositories[type_name] = repository_class
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise RegistryRepositoryRegistrationError(
                "Unable to register registry-repository implementation.",
                repository_type=type_name,
                cause=exc,
                metadata={"repository_class": repository_class.__name__},
            ) from exc

    def unregister(self, repository_type: str) -> RegistryRepositoryClass:
        type_name = normalize_registry_repository_type(repository_type)
        try:
            return self._repositories.pop(type_name)
        except KeyError as exc:
            raise RegistryRepositoryNotRegisteredError(
                f"Registry repository type is not registered: {type_name}",
                repository_type=type_name,
            ) from exc

    def get(self, repository_type: str) -> RegistryRepositoryClass:
        type_name = normalize_registry_repository_type(repository_type)
        try:
            return self._repositories[type_name]
        except KeyError as exc:
            raise RegistryRepositoryNotRegisteredError(
                f"Registry repository type is not registered: {type_name}",
                repository_type=type_name,
            ) from exc

    def is_registered(self, repository_type: str) -> bool:
        return normalize_registry_repository_type(repository_type) in self._repositories

    @property
    def registered_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._repositories))

    @property
    def count(self) -> int:
        return len(self._repositories)

    def clear(self) -> None:
        self._repositories.clear()

    def __contains__(self, repository_type: object) -> bool:
        if not isinstance(repository_type, str):
            return False
        try:
            return self.is_registered(repository_type)
        except RegistryRepositoryFactoryConfigurationError:
            return False

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[str]:
        return iter(self.registered_types)


__all__ = [
    "RegistryRepositoryClass",
    "RegistryRepositoryRegistry",
    "normalize_registry_repository_type",
]
