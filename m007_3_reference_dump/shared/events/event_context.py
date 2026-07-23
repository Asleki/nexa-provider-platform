"""
============================================================
Nexa Provider Platform
File: shared/events/event_context.py
Layer: Shared Event Engine
Milestone: NPP-M006.2.2 — Event Context
============================================================

Defines immutable execution context supplied to the Event
Engine during event processing.

The context describes *how* an event is processed rather than
the event's business payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EventContext:
    """
    Immutable execution context for event processing.

    Carries infrastructure-level execution information that
    accompanies an event through the Event Engine.
    """

    runtime_mode: str = "production"
    actor_id: str | None = None
    source: str = "npp"
    correlation_id: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        def _normalize(name: str, value: str | None, required: bool = False):
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
            self,
            "runtime_mode",
            _normalize("runtime_mode", self.runtime_mode, True),
        )
        object.__setattr__(
            self,
            "actor_id",
            _normalize("actor_id", self.actor_id),
        )
        object.__setattr__(
            self,
            "source",
            _normalize("source", self.source, True),
        )
        object.__setattr__(
            self,
            "correlation_id",
            _normalize("correlation_id", self.correlation_id),
        )

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")

        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(dict(self.attributes)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime_mode": self.runtime_mode,
            "actor_id": self.actor_id,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "attributes": dict(self.attributes),
        }


__all__ = [
    "EventContext",
]
