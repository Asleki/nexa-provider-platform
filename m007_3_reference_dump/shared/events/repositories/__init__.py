"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/__init__.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.10 — Package Exports
============================================================

Public package interface for the Shared Event Repository
Foundation.

This package exposes the stable repository contracts,
implementations, registries, metadata, factory, result objects,
types, and exception hierarchy used by higher layers.

Consumers should import from this package rather than individual
implementation modules whenever practical.
"""

from .base_event_repository import BaseEventRepository
from .event_repository_errors import (
    EVENT_REPOSITORY_ERROR_PREFIX,
    EventAlreadyRegisteredError,
    EventClearError,
    EventCountError,
    EventDataCorruptionError,
    EventDeleteError,
    EventDuplicateError,
    EventExistsError,
    EventFactoryError,
    EventIdentifierError,
    EventInvalidError,
    EventListError,
    EventNotFoundError,
    EventNotRegisteredError,
    EventReadError,
    EventRecordError,
    EventRegistrationError,
    EventRepositoryConfigurationError,
    EventRepositoryError,
    EventRepositoryInitializationError,
    EventRepositoryOperationError,
    EventSchemaError,
    EventStorageError,
    EventStoreError,
    EventUnsupportedOperationError,
)
from .event_repository_factory import EventRepositoryFactory
from .event_repository_interface import EventRepositoryInterface
from .event_repository_metadata import (
    DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY,
    MEMORY_EVENT_REPOSITORY_METADATA,
    EventRepositoryMetadata,
    EventRepositoryMetadataRegistry,
)
from .event_repository_registry import (
    EventRepositoryClass,
    EventRepositoryRegistry,
    normalize_event_repository_type,
)
from .event_repository_result import EventRepositoryResult
from .event_repository_types import (
    EventRepositoryOperation,
    EventRepositoryType,
)
from .memory_event_repository import MemoryEventRepository

__all__ = [
    # Base
    "BaseEventRepository",

    # Interface
    "EventRepositoryInterface",

    # Types
    "EventRepositoryOperation",
    "EventRepositoryType",

    # Results
    "EventRepositoryResult",

    # Registry
    "EventRepositoryClass",
    "EventRepositoryRegistry",
    "normalize_event_repository_type",

    # Factory
    "EventRepositoryFactory",

    # Metadata
    "EventRepositoryMetadata",
    "EventRepositoryMetadataRegistry",
    "MEMORY_EVENT_REPOSITORY_METADATA",
    "DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY",

    # Implementations
    "MemoryEventRepository",

    # Constants
    "EVENT_REPOSITORY_ERROR_PREFIX",

    # Errors
    "EventRepositoryError",
    "EventRepositoryConfigurationError",
    "EventRepositoryInitializationError",
    "EventRepositoryOperationError",
    "EventStoreError",
    "EventReadError",
    "EventDeleteError",
    "EventListError",
    "EventExistsError",
    "EventCountError",
    "EventClearError",
    "EventRecordError",
    "EventNotFoundError",
    "EventDuplicateError",
    "EventInvalidError",
    "EventIdentifierError",
    "EventRegistrationError",
    "EventAlreadyRegisteredError",
    "EventNotRegisteredError",
    "EventFactoryError",
    "EventUnsupportedOperationError",
    "EventStorageError",
    "EventDataCorruptionError",
    "EventSchemaError",
]