"""
============================================================
Nexa Provider Platform
File: shared/repositories/repository_factory.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Constructs repository instances through registered implementations.

Higher layers request a repository by stable repository type and
constructor arguments without importing concrete repository classes.
"""

from __future__ import annotations

from typing import Any

from .local_repository import LocalRepository
from .repository_errors import (
    RepositoryFactoryError,
    RepositoryNotRegisteredError,
)
from .repository_interface import RepositoryInterface
from .repository_registry import RepositoryRegistry
from .repository_types import RepositoryType


class RepositoryFactory:
    """Create repository instances from a ``RepositoryRegistry``."""

    def __init__(
        self,
        registry: RepositoryRegistry | None = None,
        *,
        register_defaults: bool = True,
    ) -> None:
        self._registry = (
            registry
            if registry is not None
            else RepositoryRegistry()
        )

        if register_defaults:
            self.register_defaults()

    @property
    def registry(self) -> RepositoryRegistry:
        """Return the registry used by this factory."""

        return self._registry

    def register_defaults(self) -> None:
        """Register built-in repository implementations."""

        if not self._registry.is_registered(RepositoryType.LOCAL):
            self._registry.register(
                RepositoryType.LOCAL,
                LocalRepository,
            )

    def create(
        self,
        repository_type: RepositoryType | str,
        **kwargs: Any,
    ) -> RepositoryInterface:
        """
        Construct one repository instance.

        All keyword arguments are forwarded to the registered concrete
        repository constructor.
        """

        try:
            repository_class = self._registry.get(repository_type)
        except RepositoryNotRegisteredError:
            raise
        except Exception as exc:
            raise RepositoryFactoryError(
                "Unable to resolve repository implementation.",
                repository_type=str(repository_type),
                cause=exc,
            ) from exc

        try:
            repository = repository_class(**kwargs)
        except Exception as exc:
            raise RepositoryFactoryError(
                "Unable to construct repository instance.",
                repository=(
                    str(kwargs.get("repository_name")).strip()
                    if kwargs.get("repository_name") is not None
                    else None
                ),
                repository_type=(
                    repository_type.value
                    if isinstance(repository_type, RepositoryType)
                    else str(repository_type).strip()
                ),
                cause=exc,
                metadata={
                    "repository_class": repository_class.__name__,
                    "constructor_arguments": tuple(sorted(kwargs)),
                },
            ) from exc

        if not isinstance(repository, RepositoryInterface):
            raise RepositoryFactoryError(
                (
                    "Registered repository constructor did not return "
                    "a RepositoryInterface instance."
                ),
                repository=(
                    repository.repository_name
                    if hasattr(repository, "repository_name")
                    else None
                ),
                repository_type=(
                    repository_type.value
                    if isinstance(repository_type, RepositoryType)
                    else str(repository_type).strip()
                ),
                metadata={
                    "repository_class": repository_class.__name__,
                    "actual_type": type(repository).__name__,
                },
            )

        return repository

    def create_local(
        self,
        **kwargs: Any,
    ) -> RepositoryInterface:
        """Construct a repository using the built-in local backend."""

        return self.create(
            RepositoryType.LOCAL,
            **kwargs,
        )


_default_registry = RepositoryRegistry()
_default_factory = RepositoryFactory(_default_registry)


def get_default_repository_registry() -> RepositoryRegistry:
    """Return the process-wide default repository registry."""

    return _default_registry


def get_default_repository_factory() -> RepositoryFactory:
    """Return the process-wide default repository factory."""

    return _default_factory


def create_repository(
    repository_type: RepositoryType | str,
    **kwargs: Any,
) -> RepositoryInterface:
    """Create a repository through the process-wide default factory."""

    return _default_factory.create(
        repository_type,
        **kwargs,
    )


__all__ = [
    "RepositoryFactory",
    "create_repository",
    "get_default_repository_factory",
    "get_default_repository_registry",
]