"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/base_event_repository.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.5 — Base Event Repository
============================================================

Base implementation shared by concrete event repository classes.

Provides immutable repository metadata and common validation for
event identifiers and EventEnvelope instances. Storage mechanics
remain the responsibility of concrete repository implementations.
"""

from __future__ import annotations

from abc import ABC
from typing import Any

from ..event_envelope import EventEnvelope
from .event_repository_errors import (
    EventIdentifierError,
    EventInvalidError,
    EventRepositoryConfigurationError,
)
from .event_repository_interface import EventRepositoryInterface
from .event_repository_types import EventRepositoryOperation, EventRepositoryType


class BaseEventRepository(EventRepositoryInterface, ABC):
    """
    Common foundation for event repository implementations.

    The base class owns repository identity and reusable validation.
    It deliberately does not implement persistence operations because
    storage behavior belongs to concrete repositories.
    """

    def __init__(
        self,
        repository_name: str,
        repository_type: EventRepositoryType = EventRepositoryType.MEMORY,
    ) -> None:
        """
        Initialize immutable event-repository metadata.

        Parameters
        ----------
        repository_name:
            Logical repository name used in results, diagnostics,
            registration, and audit context.

        repository_type:
            Concrete event-repository implementation type.
        """

        if not isinstance(repository_name, str):
            raise EventRepositoryConfigurationError(
                "repository_name must be a string.",
                repository_type=(
                    repository_type.value
                    if isinstance(repository_type, EventRepositoryType)
                    else None
                ),
            )

        normalized_name = repository_name.strip()

        if not normalized_name:
            raise EventRepositoryConfigurationError(
                "repository_name must not be empty.",
                repository_type=(
                    repository_type.value
                    if isinstance(repository_type, EventRepositoryType)
                    else None
                ),
            )

        if not isinstance(repository_type, EventRepositoryType):
            raise EventRepositoryConfigurationError(
                "repository_type must be an EventRepositoryType.",
                repository=normalized_name,
                metadata={
                    "received_type": type(repository_type).__name__,
                },
            )

        self._repository_name = normalized_name
        self._repository_type = repository_type

    @property
    def repository_name(self) -> str:
        """Return the logical event repository name."""

        return self._repository_name

    @property
    def repository_type(self) -> str:
        """Return the serialized repository implementation type."""

        return self._repository_type.value

    def validate_event_id(
        self,
        event_id: Any,
        *,
        operation: EventRepositoryOperation | None = None,
    ) -> str:
        """
        Validate and normalize an immutable event identifier.

        Raises
        ------
        EventIdentifierError
            If the identifier is missing, not a string, or empty.
        """

        if event_id is None:
            raise EventIdentifierError(
                "event_id must not be None.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
            )

        if not isinstance(event_id, str):
            raise EventIdentifierError(
                "event_id must be a string.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                metadata={
                    "received_type": type(event_id).__name__,
                },
            )

        normalized_event_id = event_id.strip()

        if not normalized_event_id:
            raise EventIdentifierError(
                "event_id must not be empty.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
            )

        return normalized_event_id

    def validate_envelope(
        self,
        envelope: Any,
        *,
        operation: EventRepositoryOperation = EventRepositoryOperation.STORE,
    ) -> EventEnvelope:
        """
        Validate an EventEnvelope before repository use.

        Validation confirms the envelope type and ensures that its
        immutable event identifier is valid. The original envelope is
        returned unchanged.
        """

        if not isinstance(envelope, EventEnvelope):
            raise EventInvalidError(
                "envelope must be an EventEnvelope.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                metadata={
                    "received_type": type(envelope).__name__,
                },
            )

        try:
            normalized_event_id = self.validate_event_id(
                envelope.event_id,
                operation=operation,
            )
        except EventIdentifierError as exc:
            raise EventInvalidError(
                "EventEnvelope contains an invalid event_id.",
                operation=operation,
                repository=self.repository_name,
                event_id=(
                    envelope.event_id
                    if isinstance(envelope.event_id, str)
                    else None
                ),
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

        if normalized_event_id != envelope.event_id:
            raise EventInvalidError(
                "EventEnvelope event_id must already be normalized.",
                operation=operation,
                repository=self.repository_name,
                event_id=normalized_event_id,
                repository_type=self.repository_type,
                metadata={
                    "original_event_id": envelope.event_id,
                },
            )

        return envelope


__all__ = [
    "BaseEventRepository",
]
