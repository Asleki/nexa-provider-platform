"""
============================================================
Nexa Provider Platform
Package: shared.events
Layer: Shared Event Infrastructure
============================================================

Public exports for the shared event infrastructure and
shared event engine.
"""

from .base_event import BaseEvent
from .event_context import EventContext
from .event_engine import EventEngine
from .event_engine_errors import (
    DuplicateHandlerRegistrationError,
    EventEngineError,
    HandlerExecutionError,
    HandlerNotRegisteredError,
    InvalidHandlerError,
)
from .event_envelope import EventEnvelope
from .event_errors import (
    EventConflictError,
    EventError,
    EventNotFoundError,
    EventPersistenceError,
    EventProcessingError,
    EventSerializationError,
    EventValidationError,
)
from .event_handler import EventHandler
from .event_interface import EventInterface
from .event_metadata import EventMetadata
from .event_result import EventResult
from .event_status import EventStatus
from .event_types import EventType

__all__ = [
    "BaseEvent",
    "DuplicateHandlerRegistrationError",
    "EventConflictError",
    "EventContext",
    "EventEngine",
    "EventEngineError",
    "EventEnvelope",
    "EventError",
    "EventHandler",
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
    "HandlerExecutionError",
    "HandlerNotRegisteredError",
    "InvalidHandlerError",
]
