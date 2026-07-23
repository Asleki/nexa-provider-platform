"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_factory.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.8 — Event Repository Factory
============================================================

Creates concrete event-repository instances through the event
repository registry.

The factory keeps callers independent from concrete repository
implementations. It registers the default in-memory repository while
allowing custom registries and future storage backends to be supplied
without changing higher-level event services.
"""

from __future__ import annotations

from typing import Any

from .event_repository_errors import (
    EventFactoryError,
    EventRepositoryConfigurationError,
)
from .event_repository_interface import EventRepositoryInterface
from .event_repository_registry import (
    EventRepositoryRegistry,
    normalize_event_repository_type,
)
from .event_repository_types import EventRepositoryType
from .memory_event_repository import MemoryEventRepository


class EventRepositoryFactory:
    """
    Create event repositories registered by implementation type.

    A caller may inject a custom ``EventRepositoryRegistry`` for
    testing, provider-specific configuration, or future repository
    implementations. By default, the factory registers the built-in
    in-memory repository.
    """

    def __init__(
        self,
        registry: EventRepositoryRegistry | None = None,
        *,
        register_defaults: bool = True,
    ) -> None:
        if registry is not None and not isinstance(
            registry,
            EventRepositoryRegistry,
        ):
            raise EventRepositoryConfigurationError(
                "registry must be an EventRepositoryRegistry instance.",
                metadata={
                    "actual_type": type(registry).__name__,
                },
            )

        self._registry = (
            registry
            if registry is not None
            else EventRepositoryRegistry()
        )

        if register_defaults:
            self.register_defaults()

    @property
    def registry(self) -> EventRepositoryRegistry:
        """Return the registry used by this factory."""

        return self._registry

    def register_defaults(self) -> None:
        """
        Register the built-in event-repository implementations.

        Registration is idempotent. Existing registrations are not
        replaced, allowing an injected registry to provide an explicit
        implementation for a default repository type.
        """

        if not self._registry.is_registered(EventRepositoryType.MEMORY):
            self._registry.register(
                EventRepositoryType.MEMORY,
                MemoryEventRepository,
            )

    def create(
        self,
        repository_type: EventRepositoryType | str = (
            EventRepositoryType.MEMORY
        ),
        *args: Any,
        **kwargs: Any,
    ) -> EventRepositoryInterface:
        """
        Create one registered event-repository instance.

        Positional and keyword arguments are forwarded directly to the
        selected concrete repository class. This keeps the factory
        compatible with future repositories that require backend-
        specific initialization parameters.
        """

        type_name = normalize_event_repository_type(repository_type)
        repository_class = self._registry.get(type_name)

        try:
            repository = repository_class(*args, **kwargs)
        except Exception as exc:
            raise EventFactoryError(
                "Unable to create event-repository instance.",
                repository_type=type_name,
                cause=exc,
                metadata={
                    "repository_class": repository_class.__name__,
                },
            ) from exc

        if not isinstance(repository, EventRepositoryInterface):
            raise EventFactoryError(
                (
                    "Created repository does not implement "
                    "EventRepositoryInterface."
                ),
                repository_type=type_name,
                metadata={
                    "repository_class": repository_class.__name__,
                    "actual_type": type(repository).__name__,
                },
            )

        return repository


__all__ = [
    "EventRepositoryFactory",
]
