"""
============================================================
Nexa Provider Platform
File: registries/events/registry_event.py
Layer: Master Registry Foundation
Milestone: NPP-M008.10 — Registry Events
============================================================

Immutable registry-domain event compatible with the shared M006 BaseEvent.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from shared.events import BaseEvent, EventMetadata
from shared.events.event_errors import EventValidationError

from .registry_event_type import RegistryEventType


_REQUIRED_PAYLOAD_FIELDS = ("registry_id", "registry_code", "registry_family")


class RegistryEvent(BaseEvent):
    """Concrete immutable event carrying a registry business fact."""

    def __init__(
        self,
        *,
        event_id: str,
        event_type: RegistryEventType,
        occurred_at: datetime,
        event_metadata: EventMetadata,
        payload: Mapping[str, Any],
        event_version: int = 1,
    ) -> None:
        if not isinstance(event_type, RegistryEventType):
            raise TypeError("event_type must be a RegistryEventType.")
        if not isinstance(event_metadata, EventMetadata):
            raise TypeError("event_metadata must be EventMetadata.")
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping.")

        normalized_payload = self._normalize_payload(payload)
        super().__init__(
            event_id=event_id,
            event_type=event_type.value,
            event_version=event_version,
            occurred_at=occurred_at,
            metadata=event_metadata.to_dict(),
            payload=normalized_payload,
        )
        self._registry_event_type = event_type
        self._event_metadata = event_metadata
        self.validate()

    @property
    def registry_event_type(self) -> RegistryEventType:
        return self._registry_event_type

    @property
    def event_metadata(self) -> EventMetadata:
        return self._event_metadata

    @property
    def registry_id(self) -> str:
        return str(self.payload["registry_id"])

    def validate(self) -> None:
        super().validate()
        for field in _REQUIRED_PAYLOAD_FIELDS:
            value = self.payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise EventValidationError(
                    f"payload.{field} must be non-empty text.",
                    event_id=self.event_id,
                    event_type=self.event_type,
                    metadata={"field": field},
                )

        if self.registry_event_type is RegistryEventType.REGISTRY_STATUS_CHANGED:
            for field in ("previous_status", "current_status"):
                value = self.payload.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise EventValidationError(
                        f"payload.{field} must be non-empty text.",
                        event_id=self.event_id,
                        event_type=self.event_type,
                        metadata={"field": field},
                    )
            if self.payload["previous_status"] == self.payload["current_status"]:
                raise EventValidationError(
                    "status-change events require different statuses.",
                    event_id=self.event_id,
                    event_type=self.event_type,
                )

    @staticmethod
    def _normalize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        for field in _REQUIRED_PAYLOAD_FIELDS:
            value = normalized.get(field)
            if isinstance(value, str):
                normalized[field] = value.strip()
        for field in ("previous_status", "current_status", "reason"):
            value = normalized.get(field)
            if isinstance(value, str):
                normalized[field] = value.strip()
        return normalized


__all__ = ["RegistryEvent"]
