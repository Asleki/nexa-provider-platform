"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_interface.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.1 — Event Repository Interface
============================================================

Defines the storage-independent contract implemented by all
event repository implementations.

The Event Engine and provider services depend on this contract
rather than a specific persistence backend. Concrete event
repositories may use memory, files, databases, remote services,
or future adapters without changing event-processing logic.

Previously committed event infrastructure remains unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..event_envelope import EventEnvelope

if TYPE_CHECKING:
    from .event_repository_result import EventRepositoryResult


class EventRepositoryInterface(ABC):
    """
    Abstract contract for immutable EventEnvelope persistence.

    Implementations are responsible for storage mechanics,
    duplicate-event protection, deterministic retrieval, and
    translation of backend failures into the event repository
    exception hierarchy.

    Event creation, event handling, authorization, business-rule
    validation, synchronization policy, and transport logic remain
    outside this interface.

    Event envelopes are immutable records. Therefore, this
    contract deliberately provides no update operation.
    """

    @property
    @abstractmethod
    def repository_name(self) -> str:
        """Return the logical event repository name."""

    @property
    @abstractmethod
    def repository_type(self) -> str:
        """Return the concrete event repository implementation type."""

    @abstractmethod
    def store(
        self,
        envelope: EventEnvelope,
    ) -> "EventRepositoryResult":
        """
        Persist one new EventEnvelope.

        Implementations must reject invalid envelopes and duplicate
        event identifiers. A stored envelope must not be modified
        in place after persistence.
        """

    @abstractmethod
    def get(
        self,
        event_id: str,
    ) -> "EventRepositoryResult":
        """
        Retrieve one EventEnvelope by its immutable event identifier.

        Implementations must raise an event-repository not-found
        error when the requested event does not exist.
        """

    @abstractmethod
    def list_all(self) -> "EventRepositoryResult":
        """
        Return all stored EventEnvelope objects.

        Results should use deterministic ordering where practical.
        An empty repository must return a successful result with an
        empty event collection.
        """

    @abstractmethod
    def exists(
        self,
        event_id: str,
    ) -> "EventRepositoryResult":
        """Return a successful result describing event existence."""

    @abstractmethod
    def count(self) -> "EventRepositoryResult":
        """Return a successful result containing the event count."""

    @abstractmethod
    def delete(
        self,
        event_id: str,
    ) -> "EventRepositoryResult":
        """
        Remove one stored EventEnvelope where deletion is permitted.

        Production implementations may prohibit deletion because
        event records are normally append-only. This operation exists
        primarily for controlled testing, simulation, and repository
        maintenance implementations.
        """

    @abstractmethod
    def clear(self) -> "EventRepositoryResult":
        """
        Remove all stored EventEnvelope objects where permitted.

        Production repositories may prohibit this operation. It is
        intended primarily for isolated tests and controlled
        simulation environments.
        """


__all__ = [
    "EventRepositoryInterface",
]
