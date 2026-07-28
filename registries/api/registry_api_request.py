"""Immutable framework-neutral request envelope for M008.11."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .registry_api_errors import RegistryApiValidationError
from .registry_api_operation import RegistryApiOperation


def _text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise RegistryApiValidationError(f"{name} must be a string.")
    value = value.strip()
    if not value:
        raise RegistryApiValidationError(f"{name} must not be empty.")
    return value


def _mapping(name: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RegistryApiValidationError(f"{name} must be a mapping.")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class RegistryApiRequest:
    request_id: str
    operation: RegistryApiOperation
    requested_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _text("request_id", self.request_id))
        object.__setattr__(self, "operation", RegistryApiOperation.parse(self.operation))
        if not isinstance(self.requested_at, datetime):
            raise RegistryApiValidationError("requested_at must be a datetime.")
        if self.requested_at.tzinfo is None:
            raise RegistryApiValidationError("requested_at must be timezone-aware.")
        object.__setattr__(self, "requested_at", self.requested_at.astimezone(timezone.utc))
        object.__setattr__(self, "payload", _mapping("payload", self.payload))
        object.__setattr__(self, "metadata", _mapping("metadata", self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "requested_at": self.requested_at.isoformat(),
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }


__all__ = ["RegistryApiRequest"]
