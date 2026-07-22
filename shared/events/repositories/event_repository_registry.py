"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_registry.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.7 — Event Repository Registry
============================================================

Registers concrete event-repository implementations by repository
type.

The registry keeps event services and factory callers independent
from concrete repository classes while allowing future event
repository backends to be introduced without changing higher
layers.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TypeAlias

from .event_repository_errors import (
    EventAlreadyRegisteredError,
    EventNotRegisteredError,
    EventRegistrationError,
    EventRepositoryConfigurationError,
)
from .event_repository_interface import EventRepositoryInterface
from .event_repository_types import EventRepositoryType


EventRepositoryClass: TypeAlias = type[EventRepositoryInterface]


def normalize_event_repository_type(
    repository_type: EventRepositoryType | str,
) -> str:
    """Normalize an event-repository type to its stable string value."""

    if isinstance(repository_type, EventRepositoryType):
        return repository_type.value

    value = str(repository_type).strip().lower()

    if not value:
        raise EventRepositoryConfigurationError(
            "repository_type must not be empty."
        )

    return value


class EventRepositoryRegistry:
    """
    Registry of concrete event-repository implementation classes.

    Repository types are stored by normalized string value so future
    implementations can be registered before they are added to the
    ``EventRepositoryType`` enum.
    """

    def __init__(self) -> None:
        self._repositories: dict[str, EventRepositoryClass] = {}

    def register(
        self,
        repository_type: EventRepositoryType | str,
        repository_class: EventRepositoryClass,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register an event-repository implementation class.

        Parameters
        ----------
        repository_type:
            Stable event-repository implementation type.

        repository_class:
            Concrete class implementing ``EventRepositoryInterface``.

        replace:
            When True, explicitly replace an existing registration.
        """

        type_name = normalize_event_repository_type(repository_type)

        if not isinstance(repository_class, type):
            raise EventRepositoryConfigurationError(
                "repository_class must be a class.",
                repository_type=type_name,
                metadata={
                    "actual_type": type(repository_class).__name__,
                },
            )

        if not issubclass(
            repository_class,
            EventRepositoryInterface,
        ):
            raise EventRepositoryConfigurationError(
                (
                    "repository_class must implement "
                    "EventRepositoryInterface."
                ),
                repository_type=type_name,
                metadata={
                    "repository_class": repository_class.__name__,
                },
            )

        if type_name in self._repositories and not replace:
            raise EventAlreadyRegisteredError(
                (
                    "Event repository type is already registered: "
                    f"{type_name}"
                ),
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
            raise EventRegistrationError(
                "Unable to register event-repository implementation.",
                repository_type=type_name,
                cause=exc,
                metadata={
                    "repository_class": repository_class.__name__,
                },
            ) from exc

    def unregister(
        self,
        repository_type: EventRepositoryType | str,
    ) -> EventRepositoryClass:
        """Remove and return a registered implementation class."""

        type_name = normalize_event_repository_type(repository_type)

        try:
            return self._repositories.pop(type_name)
        except KeyError as exc:
            raise EventNotRegisteredError(
                (
                    "Event repository type is not registered: "
                    f"{type_name}"
                ),
                repository_type=type_name,
            ) from exc

    def get(
        self,
        repository_type: EventRepositoryType | str,
    ) -> EventRepositoryClass:
        """Return the class registered for an event-repository type."""

        type_name = normalize_event_repository_type(repository_type)

        try:
            return self._repositories[type_name]
        except KeyError as exc:
            raise EventNotRegisteredError(
                (
                    "Event repository type is not registered: "
                    f"{type_name}"
                ),
                repository_type=type_name,
            ) from exc

    def is_registered(
        self,
        repository_type: EventRepositoryType | str,
    ) -> bool:
        """Return True when an event-repository type is registered."""

        type_name = normalize_event_repository_type(repository_type)
        return type_name in self._repositories

    @property
    def registered_types(self) -> tuple[str, ...]:
        """Return registered types in deterministic order."""

        return tuple(sorted(self._repositories))

    @property
    def count(self) -> int:
        """Return the number of registered event-repository types."""

        return len(self._repositories)

    def clear(self) -> None:
        """Remove all event-repository registrations."""

        self._repositories.clear()

    def __contains__(
        self,
        repository_type: object,
    ) -> bool:
        if not isinstance(
            repository_type,
            (EventRepositoryType, str),
        ):
            return False

        try:
            return self.is_registered(repository_type)
        except EventRepositoryConfigurationError:
            return False

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[str]:
        return iter(self.registered_types)


__all__ = [
    "EventRepositoryClass",
    "EventRepositoryRegistry",
    "normalize_event_repository_type",
]
