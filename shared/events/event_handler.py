"""
============================================================
Nexa Provider Platform
File: shared/events/event_handler.py
Layer: Shared Event Engine
Milestone: NPP-M006.2.1 — Event Handler
============================================================

Defines the abstract contract implemented by every Event
Handler within the Nexa Provider Platform.

Handlers contain event-specific processing logic while the
Event Engine is responsible for validation, handler
resolution, execution, and returning EventResult.

Handlers must remain deterministic and side-effect aware.
They must not mutate incoming event objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .event_interface import EventInterface
from .event_result import EventResult


TEvent = TypeVar("TEvent", bound=EventInterface)


class EventHandler(ABC, Generic[TEvent]):
    """
    Abstract processing contract for platform events.

    Concrete implementations process exactly one category
    of EventInterface implementation and return an
    EventResult describing the outcome.

    Event handlers are intentionally unaware of handler
    registration, routing, synchronization, persistence,
    transport, or repository concerns.
    """

    @property
    @abstractmethod
    def event_type(self) -> str:
        """
        Return the event type handled by this handler.

        The returned value is used by the Event Engine
        when resolving handlers.
        """

    @abstractmethod
    def can_handle(
        self,
        event: EventInterface,
    ) -> bool:
        """
        Return True if this handler supports the supplied
        event instance.

        Implementations must not mutate the event.
        """

    @abstractmethod
    def handle(
        self,
        event: TEvent,
    ) -> EventResult:
        """
        Process the supplied event.

        Implementations should return an EventResult for
        both successful and expected processing outcomes.

        Infrastructure failures should be raised as
        EventProcessingError (or derived exceptions)
        rather than converted into EventResult.
        """


__all__ = [
    "EventHandler",
]