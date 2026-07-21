"""
============================================================
Nexa Provider Platform
File: shared/events/event_errors.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.4 — Event Errors
============================================================

Defines the exception hierarchy used by the Event
Infrastructure.

Event exceptions communicate failed event operations while
EventResult represents completed lifecycle outcomes.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


class EventError(Exception):
    """
    Base exception for Event Infrastructure failures.

    Parameters
    ----------
    message:
        Human-readable error description.

    event_id:
        Identifier of the affected event, when known.

    event_type:
        Stable type name of the affected event, when known.

    metadata:
        Additional implementation-neutral error context.
    """

    def __init__(
        self,
        message: str,
        *,
        event_id: str | None = None,
        event_type: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if not isinstance(message, str):
            raise TypeError("message must be a string.")

        normalized_message = message.strip()

        if not normalized_message:
            raise ValueError("message must not be empty.")

        if event_id is not None:
            if not isinstance(event_id, str):
                raise TypeError("event_id must be a string.")

            event_id = event_id.strip()

            if not event_id:
                raise ValueError(
                    "event_id must not be empty when provided."
                )

        if event_type is not None:
            if not isinstance(event_type, str):
                raise TypeError("event_type must be a string.")

            event_type = event_type.strip()

            if not event_type:
                raise ValueError(
                    "event_type must not be empty when provided."
                )

        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        super().__init__(normalized_message)

        self._message = normalized_message
        self._event_id = event_id
        self._event_type = event_type
        self._metadata = MappingProxyType(dict(metadata or {}))

    @property
    def message(self) -> str:
        """Return the human-readable error description."""

        return self._message

    @property
    def event_id(self) -> str | None:
        """Return the affected event identifier, when known."""

        return self._event_id

    @property
    def event_type(self) -> str | None:
        """Return the affected event type, when known."""

        return self._event_type

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Return immutable implementation-neutral context."""

        return self._metadata

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error into a detached plain dictionary."""

        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "metadata": dict(self.metadata),
        }


class EventValidationError(EventError):
    """Raised when an event violates its required contract."""


class EventSerializationError(EventError):
    """Raised when event serialization or deserialization fails."""


class EventPersistenceError(EventError):
    """Raised when an event cannot be persisted or retrieved."""


class EventProcessingError(EventError):
    """Raised when event processing fails after validation."""


class EventNotFoundError(EventError):
    """Raised when a requested event cannot be located."""


class EventConflictError(EventError):
    """Raised when an event conflicts with existing event state."""


__all__ = [
    "EventConflictError",
    "EventError",
    "EventNotFoundError",
    "EventPersistenceError",
    "EventProcessingError",
    "EventSerializationError",
    "EventValidationError",
]
