"""
============================================================
Nexa Provider Platform
File: shared/events/event_interface.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.1 — Event Interface
============================================================

Defines the implementation-independent contract that every
platform event must satisfy.

Provider domains, identity registries, audit infrastructure,
synchronization services, CLI commands, and REST APIs depend on
this interface rather than concrete event implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Mapping


class EventInterface(ABC):
    """
    Abstract contract for immutable Nexa Provider Platform events.

    Implementations are responsible for exposing stable event
    identity, type, version, occurrence time, metadata, and
    payload values. They must also support validation and
    deterministic conversion into transport-safe representations.

    Domain-specific business rules, persistence, audit recording,
    authorization, synchronization policy, and transport delivery
    remain outside this interface.
    """

    @property
    @abstractmethod
    def event_id(self) -> str:
        """Return the immutable unique identifier of the event."""

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the stable event type name."""

    @property
    @abstractmethod
    def event_version(self) -> int:
        """Return the positive schema version of the event."""

    @property
    @abstractmethod
    def occurred_at(self) -> datetime:
        """Return when the represented action occurred."""

    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        """Return immutable implementation-neutral event metadata."""

    @property
    @abstractmethod
    def payload(self) -> Mapping[str, Any]:
        """Return the immutable business payload carried by the event."""

    @abstractmethod
    def validate(self) -> None:
        """
        Validate the complete event contract.

        Implementations must raise an event validation exception
        when the event is invalid. Successful validation returns
        ``None`` and must not mutate event state.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Convert the event into a plain dictionary.

        The returned dictionary must contain transport-safe values
        and must not expose mutable internal event state.
        """

    @abstractmethod
    def serialize(self) -> str:
        """
        Serialize the event into a deterministic string format.

        Concrete implementations may initially use JSON while
        preserving this storage- and transport-independent
        interface.
        """


__all__ = [
    "EventInterface",
]
