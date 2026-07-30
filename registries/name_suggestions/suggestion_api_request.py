"""Immutable framework-neutral request envelope for M009.2.8."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from .suggestion_api_errors import SuggestionApiValidationError
from .suggestion_api_operation import SuggestionApiOperation
from .suggestion_support import normalize_runtime_mode


def _mapping(name: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SuggestionApiValidationError(f"{name} must be a mapping.")
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class SuggestionApiRequest:
    request_id: str
    operation: SuggestionApiOperation
    requested_at: datetime
    runtime_mode: str = "simulation"
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise SuggestionApiValidationError("request_id must be non-empty text.")
        object.__setattr__(self, "request_id", self.request_id.strip())
        try:
            operation = SuggestionApiOperation.parse(self.operation)
            runtime_mode = normalize_runtime_mode(self.runtime_mode)
        except (TypeError, ValueError) as exc:
            raise SuggestionApiValidationError(str(exc)) from exc
        object.__setattr__(self, "operation", operation)
        object.__setattr__(self, "runtime_mode", runtime_mode)
        if not isinstance(self.requested_at, datetime) or self.requested_at.tzinfo is None:
            raise SuggestionApiValidationError("requested_at must be timezone-aware datetime.")
        object.__setattr__(self, "requested_at", self.requested_at.astimezone(timezone.utc))
        object.__setattr__(self, "payload", _mapping("payload", self.payload))
        object.__setattr__(self, "metadata", _mapping("metadata", self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "requested_at": self.requested_at.isoformat(),
            "runtime_mode": self.runtime_mode,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }


__all__ = ["SuggestionApiRequest"]
