"""
============================================================
Nexa Provider Platform
File: registries/events/registry_event_factory.py
Layer: Master Registry Foundation
Milestone: NPP-M008.10 — Registry Events
============================================================

Deterministic construction boundary for registry-domain events. Identifier
and clock providers are injectable so tests and callers remain reproducible.
============================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from registries.core import BaseRegistry, RegistryStatus
from registries.governance import RegistryLifecycleResult
from shared.events import EventMetadata

from .registry_event import RegistryEvent
from .registry_event_type import RegistryEventType

EventIdFactory = Callable[[], str]
Clock = Callable[[], datetime]


class RegistryEventFactory:
    """Create validated registry events without publishing or persisting them."""

    def __init__(
        self,
        *,
        event_id_factory: EventIdFactory | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._event_id_factory = event_id_factory or (lambda: str(uuid4()))
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def registered(
        self,
        registry: BaseRegistry,
        *,
        metadata: EventMetadata,
        attributes: Mapping[str, Any] | None = None,
    ) -> RegistryEvent:
        return self._create(
            RegistryEventType.REGISTRY_REGISTERED,
            registry,
            metadata=metadata,
            attributes=attributes,
        )

    def replaced(
        self,
        registry: BaseRegistry,
        *,
        metadata: EventMetadata,
        attributes: Mapping[str, Any] | None = None,
    ) -> RegistryEvent:
        return self._create(
            RegistryEventType.REGISTRY_REPLACED,
            registry,
            metadata=metadata,
            attributes=attributes,
        )

    def removed(
        self,
        registry: BaseRegistry,
        *,
        metadata: EventMetadata,
        attributes: Mapping[str, Any] | None = None,
    ) -> RegistryEvent:
        return self._create(
            RegistryEventType.REGISTRY_REMOVED,
            registry,
            metadata=metadata,
            attributes=attributes,
        )

    def status_changed(
        self,
        result: RegistryLifecycleResult,
        *,
        metadata: EventMetadata,
        reason: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> RegistryEvent:
        if not isinstance(result, RegistryLifecycleResult):
            raise TypeError("result must be a RegistryLifecycleResult.")
        if not result.changed:
            raise ValueError("A no-op lifecycle result cannot emit a status-change event.")

        extra = dict(attributes or {})
        extra.update(
            {
                "previous_status": result.previous_status.value,
                "current_status": result.current_status.value,
            }
        )
        if reason is not None:
            if not isinstance(reason, str):
                raise TypeError("reason must be text when provided.")
            normalized_reason = reason.strip()
            if normalized_reason:
                extra["reason"] = normalized_reason

        return self._create(
            RegistryEventType.REGISTRY_STATUS_CHANGED,
            result.registry,
            metadata=metadata,
            attributes=extra,
        )

    def _create(
        self,
        event_type: RegistryEventType,
        registry: BaseRegistry,
        *,
        metadata: EventMetadata,
        attributes: Mapping[str, Any] | None,
    ) -> RegistryEvent:
        if not isinstance(registry, BaseRegistry):
            raise TypeError("registry must be a BaseRegistry.")
        if not isinstance(metadata, EventMetadata):
            raise TypeError("metadata must be EventMetadata.")
        if attributes is not None and not isinstance(attributes, Mapping):
            raise TypeError("attributes must be a mapping when provided.")

        occurred_at = self._clock()
        if not isinstance(occurred_at, datetime):
            raise TypeError("clock must return a datetime.")
        if occurred_at.tzinfo is None:
            raise ValueError("clock must return a timezone-aware datetime.")

        event_id = self._event_id_factory()
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id_factory must return non-empty text.")

        payload = self._registry_payload(registry)
        payload.update(dict(attributes or {}))
        return RegistryEvent(
            event_id=event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            event_metadata=metadata,
            payload=payload,
        )

    @staticmethod
    def _registry_payload(registry: BaseRegistry) -> dict[str, Any]:
        definition = registry.definition
        return {
            "registry_id": registry.registry_id,
            "registry_code": definition.registry_code,
            "registry_name": definition.registry_name,
            "registry_family": definition.family.value,
            "registry_status": registry.status.value,
            "registry_version": registry.version,
        }


__all__ = ["Clock", "EventIdFactory", "RegistryEventFactory"]
