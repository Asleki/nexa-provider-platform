"""
============================================================
Nexa Provider Platform
File: shared/repositories/repository_registry.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Registers concrete repository implementations by repository type.

The registry keeps Provider Services and factory callers
independent from concrete repository classes while supporting
future repository backends without changing higher layers.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypeAlias

from .repository_errors import (
    RepositoryAlreadyRegisteredError,
    RepositoryConfigurationError,
    RepositoryNotRegisteredError,
    RepositoryRegistrationError,
)
from .repository_interface import RepositoryInterface
from .repository_types import RepositoryType


RepositoryClass: TypeAlias = type[RepositoryInterface]


def normalize_repository_type(
    repository_type: RepositoryType | str,
) -> str:
    """Normalize a repository type into its stable string value."""

    if isinstance(repository_type, RepositoryType):
        return repository_type.value

    value = str(repository_type).strip().lower()

    if not value:
        raise RepositoryConfigurationError(
            "repository_type must not be empty."
        )

    return value


class RepositoryRegistry:
    """
    Registry of concrete repository implementation classes.

    Repository types are stored by normalized string value so later
    implementations can be registered before they are added to the
    ``RepositoryType`` enum.
    """

    def __init__(self) -> None:
        self._repositories: dict[str, RepositoryClass] = {}

    def register(
        self,
        repository_type: RepositoryType | str,
        repository_class: RepositoryClass,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register a repository implementation class.

        Parameters
        ----------
        repository_type:
            Stable repository implementation type.

        repository_class:
            Concrete class implementing ``RepositoryInterface``.

        replace:
            When True, replace an existing registration explicitly.
        """

        type_name = normalize_repository_type(repository_type)

        if not isinstance(repository_class, type):
            raise RepositoryConfigurationError(
                "repository_class must be a class.",
                repository_type=type_name,
                metadata={
                    "actual_type": type(repository_class).__name__,
                },
            )

        if not issubclass(repository_class, RepositoryInterface):
            raise RepositoryConfigurationError(
                (
                    "repository_class must implement "
                    "RepositoryInterface."
                ),
                repository_type=type_name,
                metadata={
                    "repository_class": repository_class.__name__,
                },
            )

        if type_name in self._repositories and not replace:
            raise RepositoryAlreadyRegisteredError(
                f"Repository type is already registered: {type_name}",
                repository_type=type_name,
                metadata={
                    "repository_class": (
                        self._repositories[type_name].__name__
                    ),
                },
            )

        try:
            self._repositories[type_name] = repository_class
        except Exception as exc:
            raise RepositoryRegistrationError(
                "Unable to register repository implementation.",
                repository_type=type_name,
                cause=exc,
                metadata={
                    "repository_class": repository_class.__name__,
                },
            ) from exc

    def unregister(
        self,
        repository_type: RepositoryType | str,
    ) -> RepositoryClass:
        """Remove and return a registered repository implementation."""

        type_name = normalize_repository_type(repository_type)

        try:
            return self._repositories.pop(type_name)
        except KeyError as exc:
            raise RepositoryNotRegisteredError(
                f"Repository type is not registered: {type_name}",
                repository_type=type_name,
            ) from exc

    def get(
        self,
        repository_type: RepositoryType | str,
    ) -> RepositoryClass:
        """Return the class registered for a repository type."""

        type_name = normalize_repository_type(repository_type)

        try:
            return self._repositories[type_name]
        except KeyError as exc:
            raise RepositoryNotRegisteredError(
                f"Repository type is not registered: {type_name}",
                repository_type=type_name,
            ) from exc

    def is_registered(
        self,
        repository_type: RepositoryType | str,
    ) -> bool:
        """Return True when a repository type is registered."""

        type_name = normalize_repository_type(repository_type)
        return type_name in self._repositories

    @property
    def registered_types(self) -> tuple[str, ...]:
        """Return registered repository types in deterministic order."""

        return tuple(sorted(self._repositories))

    @property
    def count(self) -> int:
        """Return the number of registered repository types."""

        return len(self._repositories)

    def clear(self) -> None:
        """Remove all repository registrations."""

        self._repositories.clear()

    def __contains__(
        self,
        repository_type: object,
    ) -> bool:
        if not isinstance(repository_type, (RepositoryType, str)):
            return False

        try:
            return self.is_registered(repository_type)
        except RepositoryConfigurationError:
            return False

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[str]:
        return iter(self.registered_types)


__all__ = [
    "RepositoryClass",
    "RepositoryRegistry",
    "normalize_repository_type",
]
