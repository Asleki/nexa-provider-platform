"""Immutable framework-neutral response envelope for M008.11."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from registries.events import RegistryEvent

from .registry_api_errors import RegistryApiResultError
from .registry_api_operation import RegistryApiOperation


def _optional_mapping(name: str, value: Mapping[str, Any] | None):
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise RegistryApiResultError(f"{name} must be a mapping when provided.")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class RegistryApiResponse:
    request_id: str
    operation: RegistryApiOperation
    completed_at: datetime
    success: bool
    data: Mapping[str, Any] | None = None
    error: Mapping[str, Any] | None = None
    events: tuple[RegistryEvent, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise RegistryApiResultError("request_id must be non-empty text.")
        object.__setattr__(self, "request_id", self.request_id.strip())
        try:
            operation = RegistryApiOperation.parse(self.operation)
        except Exception as exc:
            raise RegistryApiResultError(str(exc)) from exc
        object.__setattr__(self, "operation", operation)
        if not isinstance(self.completed_at, datetime) or self.completed_at.tzinfo is None:
            raise RegistryApiResultError("completed_at must be timezone-aware datetime.")
        object.__setattr__(self, "completed_at", self.completed_at.astimezone(timezone.utc))
        if not isinstance(self.success, bool):
            raise RegistryApiResultError("success must be a bool.")
        data = _optional_mapping("data", self.data)
        error = _optional_mapping("error", self.error)
        if self.success and error is not None:
            raise RegistryApiResultError("successful responses must not contain error.")
        if not self.success and (data is not None or error is None):
            raise RegistryApiResultError("failed responses require error and no data.")
        events = tuple(self.events)
        if any(not isinstance(event, RegistryEvent) for event in events):
            raise RegistryApiResultError("events must contain only RegistryEvent instances.")
        if not self.success and events:
            raise RegistryApiResultError("failed responses must not contain events.")
        if not isinstance(self.metadata, Mapping):
            raise RegistryApiResultError("metadata must be a mapping.")
        object.__setattr__(self, "data", data)
        object.__setattr__(self, "error", error)
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def succeeded(cls, *, request_id, operation, completed_at, data=None, events=(), metadata=None):
        return cls(request_id, operation, completed_at, True, {} if data is None else data,
                   events=tuple(events), metadata={} if metadata is None else metadata)

    @classmethod
    def failed(cls, *, request_id, operation, completed_at, error, metadata=None):
        return cls(request_id, operation, completed_at, False, error=error,
                   metadata={} if metadata is None else metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "completed_at": self.completed_at.isoformat(),
            "success": self.success,
            "data": None if self.data is None else dict(self.data),
            "error": None if self.error is None else dict(self.error),
            "events": [event.to_dict() for event in self.events],
            "metadata": dict(self.metadata),
        }


__all__ = ["RegistryApiResponse"]
