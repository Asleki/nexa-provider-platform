"""
============================================================
Nexa Provider Platform
Package: shared.events
Layer: Shared Event Infrastructure
============================================================

Public exports for the shared event infrastructure.
"""

from .base_event import BaseEvent
from .event_errors import (
    EventConflictError,
    EventError,
    EventNotFoundError,
    EventPersistenceError,
    EventProcessingError,
    EventSerializationError,
    EventValidationError,
)
from .event_interface import EventInterface
from .event_metadata import EventMetadata
from .event_result import EventResult
from .event_status import EventStatus
from .event_types import EventType

__all__ = [
    "BaseEvent",
    "EventConflictError",
    "EventError",
    "EventInterface",
    "EventMetadata",
    "EventNotFoundError",
    "EventPersistenceError",
    "EventProcessingError",
    "EventResult",
    "EventSerializationError",
    "EventStatus",
    "EventType",
    "EventValidationError",
]
