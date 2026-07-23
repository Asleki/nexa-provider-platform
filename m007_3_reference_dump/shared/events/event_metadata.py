"""
============================================================
Nexa Provider Platform
File: shared/events/event_metadata.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.7 — Event Metadata
============================================================

Defines the immutable metadata attached to every platform event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EventMetadata:
    """
    Immutable infrastructure metadata describing an event.

    This information is infrastructure-focused and intentionally
    excludes business payload fields.
    """

    correlation_id: str
    causation_id: str | None = None
    actor_id: str | None = None
    device_id: str | None = None
    source: str = "npp"
    version: str = "1.0"
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        def _normalize(name: str, value: str | None, required: bool=False):
            if value is None:
                if required:
                    raise ValueError(f"{name} is required.")
                return None
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string.")
            value = value.strip()
            if required and not value:
                raise ValueError(f"{name} must not be empty.")
            return value or None

        object.__setattr__(
            self, "correlation_id",
            _normalize("correlation_id", self.correlation_id, True)
        )
        object.__setattr__(
            self, "causation_id",
            _normalize("causation_id", self.causation_id)
        )
        object.__setattr__(
            self, "actor_id",
            _normalize("actor_id", self.actor_id)
        )
        object.__setattr__(
            self, "device_id",
            _normalize("device_id", self.device_id)
        )
        object.__setattr__(
            self, "source",
            _normalize("source", self.source, True)
        )
        object.__setattr__(
            self, "version",
            _normalize("version", self.version, True)
        )

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime.")

        dt = self.created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        object.__setattr__(self, "created_at", dt)

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")

        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(dict(self.attributes))
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata to a detached dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "actor_id": self.actor_id,
            "device_id": self.device_id,
            "source": self.source,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "attributes": dict(self.attributes),
        }


__all__ = ["EventMetadata"]
