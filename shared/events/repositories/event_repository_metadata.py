"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_metadata.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.9 — Event Repository Metadata
============================================================

Defines immutable descriptive metadata for event-repository
implementations and a dedicated metadata registry.

Metadata allows higher layers, diagnostics, configuration tools,
administration services, and future provider services to inspect
repository capabilities without importing or understanding concrete
repository classes.

This module does not create repositories and does not register
repository implementation classes. Repository creation remains the
responsibility of EventRepositoryFactory, while implementation-class
registration remains the responsibility of EventRepositoryRegistry.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .event_repository_errors import (
    EventAlreadyRegisteredError,
    EventNotRegisteredError,
    EventRegistrationError,
    EventRepositoryConfigurationError,
)
from .event_repository_registry import normalize_event_repository_type
from .event_repository_types import EventRepositoryType


def _normalize_non_empty_string(
    value: Any,
    *,
    field_name: str,
) -> str:
    """Validate and normalize a required non-empty string."""

    if not isinstance(value, str):
        raise EventRepositoryConfigurationError(
            f"{field_name} must be a string.",
            metadata={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    normalized = value.strip()

    if not normalized:
        raise EventRepositoryConfigurationError(
            f"{field_name} must not be empty.",
            metadata={"field": field_name},
        )

    return normalized


def _normalize_string_tuple(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    """
    Validate, normalize, de-duplicate, and freeze string values.

    Order is preserved according to the caller-provided iterable.
    """

    if isinstance(values, (str, bytes)):
        raise EventRepositoryConfigurationError(
            f"{field_name} must be an iterable of strings.",
            metadata={
                "field": field_name,
                "actual_type": type(values).__name__,
            },
        )

    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise EventRepositoryConfigurationError(
            f"{field_name} must be an iterable of strings.",
            metadata={
                "field": field_name,
                "actual_type": type(values).__name__,
            },
            cause=exc,
        ) from exc

    normalized_values: list[str] = []
    seen: set[str] = set()

    for index, value in enumerate(raw_values):
        normalized = _normalize_non_empty_string(
            value,
            field_name=f"{field_name}[{index}]",
        )

        if normalized not in seen:
            seen.add(normalized)
            normalized_values.append(normalized)

    return tuple(normalized_values)


@dataclass(frozen=True, slots=True)
class EventRepositoryMetadata:
    """Immutable description of one event-repository implementation."""

    repository_type: str
    display_name: str
    description: str
    persistent: bool
    thread_safe: bool
    ordering_guarantee: str
    intended_uses: tuple[str, ...]
    production_ready: bool
    supports_delete: bool
    supports_clear: bool
    durable: bool
    transactional: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate, normalize, and freeze metadata state."""

        normalized_type = normalize_event_repository_type(
            self.repository_type
        )
        normalized_display_name = _normalize_non_empty_string(
            self.display_name,
            field_name="display_name",
        )
        normalized_description = _normalize_non_empty_string(
            self.description,
            field_name="description",
        )
        normalized_ordering = _normalize_non_empty_string(
            self.ordering_guarantee,
            field_name="ordering_guarantee",
        )
        normalized_uses = _normalize_string_tuple(
            self.intended_uses,
            field_name="intended_uses",
        )

        if not normalized_uses:
            raise EventRepositoryConfigurationError(
                "intended_uses must contain at least one value.",
                repository_type=normalized_type,
            )

        boolean_fields = {
            "persistent": self.persistent,
            "thread_safe": self.thread_safe,
            "production_ready": self.production_ready,
            "supports_delete": self.supports_delete,
            "supports_clear": self.supports_clear,
            "durable": self.durable,
            "transactional": self.transactional,
        }

        for field_name, value in boolean_fields.items():
            if not isinstance(value, bool):
                raise EventRepositoryConfigurationError(
                    f"{field_name} must be a boolean.",
                    repository_type=normalized_type,
                    metadata={
                        "field": field_name,
                        "actual_type": type(value).__name__,
                    },
                )

        if not isinstance(self.metadata, Mapping):
            raise EventRepositoryConfigurationError(
                "metadata must be a mapping.",
                repository_type=normalized_type,
                metadata={
                    "actual_type": type(self.metadata).__name__,
                },
            )

        if self.durable and not self.persistent:
            raise EventRepositoryConfigurationError(
                "A durable event repository must also be persistent.",
                repository_type=normalized_type,
            )

        if self.production_ready and not self.durable:
            raise EventRepositoryConfigurationError(
                "A production-ready event repository must be durable.",
                repository_type=normalized_type,
            )

        object.__setattr__(self, "repository_type", normalized_type)
        object.__setattr__(
            self,
            "display_name",
            normalized_display_name,
        )
        object.__setattr__(
            self,
            "description",
            normalized_description,
        )
        object.__setattr__(
            self,
            "ordering_guarantee",
            normalized_ordering,
        )
        object.__setattr__(
            self,
            "intended_uses",
            normalized_uses,
        )
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata into a plain dictionary."""

        return {
            "repository_type": self.repository_type,
            "display_name": self.display_name,
            "description": self.description,
            "persistent": self.persistent,
            "thread_safe": self.thread_safe,
            "ordering_guarantee": self.ordering_guarantee,
            "intended_uses": list(self.intended_uses),
            "production_ready": self.production_ready,
            "supports_delete": self.supports_delete,
            "supports_clear": self.supports_clear,
            "durable": self.durable,
            "transactional": self.transactional,
            "metadata": dict(self.metadata),
        }


class EventRepositoryMetadataRegistry:
    """
    Registry of immutable event-repository metadata records.

    The registry mirrors ``EventRepositoryRegistry`` conventions while
    remaining independent from repository implementation registration
    and repository creation.
    """

    def __init__(self) -> None:
        self._metadata: dict[str, EventRepositoryMetadata] = {}

    def register(
        self,
        metadata: EventRepositoryMetadata,
        *,
        replace: bool = False,
    ) -> None:
        """Register one event-repository metadata record."""

        if not isinstance(metadata, EventRepositoryMetadata):
            raise EventRepositoryConfigurationError(
                "metadata must be an EventRepositoryMetadata instance.",
                metadata={
                    "actual_type": type(metadata).__name__,
                },
            )

        type_name = metadata.repository_type

        if type_name in self._metadata and not replace:
            raise EventAlreadyRegisteredError(
                (
                    "Event repository metadata is already registered: "
                    f"{type_name}"
                ),
                repository_type=type_name,
                metadata={
                    "display_name": (
                        self._metadata[type_name].display_name
                    ),
                },
            )

        try:
            self._metadata[type_name] = metadata
        except Exception as exc:
            raise EventRegistrationError(
                "Unable to register event-repository metadata.",
                repository_type=type_name,
                cause=exc,
                metadata={"display_name": metadata.display_name},
            ) from exc

    def unregister(
        self,
        repository_type: EventRepositoryType | str,
    ) -> EventRepositoryMetadata:
        """Remove and return metadata for a repository type."""

        type_name = normalize_event_repository_type(repository_type)

        try:
            return self._metadata.pop(type_name)
        except KeyError as exc:
            raise EventNotRegisteredError(
                (
                    "Event repository metadata is not registered: "
                    f"{type_name}"
                ),
                repository_type=type_name,
            ) from exc

    def get(
        self,
        repository_type: EventRepositoryType | str,
    ) -> EventRepositoryMetadata:
        """Return metadata registered for a repository type."""

        type_name = normalize_event_repository_type(repository_type)

        try:
            return self._metadata[type_name]
        except KeyError as exc:
            raise EventNotRegisteredError(
                (
                    "Event repository metadata is not registered: "
                    f"{type_name}"
                ),
                repository_type=type_name,
            ) from exc

    def is_registered(
        self,
        repository_type: EventRepositoryType | str,
    ) -> bool:
        """Return True when metadata exists for a repository type."""

        type_name = normalize_event_repository_type(repository_type)
        return type_name in self._metadata

    @property
    def registered_types(self) -> tuple[str, ...]:
        """Return registered metadata types in deterministic order."""

        return tuple(sorted(self._metadata))

    @property
    def count(self) -> int:
        """Return the number of registered metadata records."""

        return len(self._metadata)

    def list_all(self) -> tuple[EventRepositoryMetadata, ...]:
        """Return all metadata records in deterministic type order."""

        return tuple(
            self._metadata[type_name]
            for type_name in self.registered_types
        )

    def clear(self) -> None:
        """Remove all metadata registrations."""

        self._metadata.clear()

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


MEMORY_EVENT_REPOSITORY_METADATA = EventRepositoryMetadata(
    repository_type=EventRepositoryType.MEMORY.value,
    display_name="In-Memory Event Repository",
    description=(
        "Thread-safe, process-local EventEnvelope repository used for "
        "testing, controlled simulation, development, and early "
        "integration."
    ),
    persistent=False,
    thread_safe=True,
    ordering_guarantee="Insertion order",
    intended_uses=(
        "testing",
        "simulation",
        "development",
        "early_integration",
    ),
    production_ready=False,
    supports_delete=True,
    supports_clear=True,
    durable=False,
    transactional=False,
    metadata={
        "storage_location": "process_memory",
        "record_model": "immutable_event_envelope",
        "process_restart_retention": False,
    },
)


DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY = (
    EventRepositoryMetadataRegistry()
)
DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY.register(
    MEMORY_EVENT_REPOSITORY_METADATA
)


__all__ = [
    "EventRepositoryMetadata",
    "EventRepositoryMetadataRegistry",
    "MEMORY_EVENT_REPOSITORY_METADATA",
    "DEFAULT_EVENT_REPOSITORY_METADATA_REGISTRY",
]
