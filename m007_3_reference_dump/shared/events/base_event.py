"""
============================================================
Nexa Provider Platform
File: shared/events/base_event.py
Layer: Shared Event Infrastructure
Milestone: NPP-M006.1.2 — Base Event
Revision: v2
============================================================
"""

from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone
import json
from types import MappingProxyType
from typing import Any, Mapping

from .event_errors import EventValidationError
from .event_interface import EventInterface


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an immutable shallow copy of a mapping."""
    return MappingProxyType(dict(value))


class BaseEvent(EventInterface, ABC):
    """Common immutable foundation for concrete event classes."""

    def __init__(
        self,
        *,
        event_id: str,
        event_type: str,
        event_version: int,
        occurred_at: datetime,
        metadata: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> None:
        if not isinstance(event_id, str):
            raise TypeError("event_id must be a string.")

        normalized_event_id = event_id.strip()
        if not normalized_event_id:
            raise ValueError("event_id must not be empty.")

        if not isinstance(event_type, str):
            raise TypeError("event_type must be a string.")

        normalized_event_type = event_type.strip()
        if not normalized_event_type:
            raise ValueError("event_type must not be empty.")

        if isinstance(event_version, bool) or not isinstance(event_version, int):
            raise TypeError("event_version must be an integer.")

        if event_version < 1:
            raise ValueError("event_version must be greater than zero.")

        if not isinstance(occurred_at, datetime):
            raise TypeError("occurred_at must be a datetime.")

        if occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware.")

        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        if payload is not None and not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping.")

        self._event_id = normalized_event_id
        self._event_type = normalized_event_type
        self._event_version = event_version
        self._occurred_at = occurred_at.astimezone(timezone.utc)
        self._metadata = _freeze_mapping(metadata or {})
        self._payload = _freeze_mapping(payload or {})

    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def event_version(self) -> int:
        return self._event_version

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self._metadata

    @property
    def payload(self) -> Mapping[str, Any]:
        return self._payload

    def validate(self) -> None:
        if not self._event_id:
            raise EventValidationError(
                "event_id must not be empty.",
                event_id=self._event_id or None,
                event_type=self._event_type or None,
            )

        if not self._event_type:
            raise EventValidationError(
                "event_type must not be empty.",
                event_id=self._event_id or None,
                event_type=self._event_type or None,
            )

        if self._event_version < 1:
            raise EventValidationError(
                "event_version must be greater than zero.",
                event_id=self._event_id,
                event_type=self._event_type,
                metadata={"event_version": self._event_version},
            )

        if self._occurred_at.tzinfo is None:
            raise EventValidationError(
                "occurred_at must be timezone-aware.",
                event_id=self._event_id,
                event_type=self._event_type,
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": dict(self.metadata),
            "payload": dict(self.payload),
        }

    def serialize(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


__all__ = ["BaseEvent"]
