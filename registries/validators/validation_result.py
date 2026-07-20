
"""
registries.validators.validation_result

Immutable container for registry validation outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .validation_message import RegistryValidationMessage


@dataclass(frozen=True, slots=True)
class RegistryValidationResult:
    """Immutable result returned by registry validators."""

    valid: bool
    messages: Tuple[RegistryValidationMessage, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def is_valid(self) -> bool:
        return self.valid

    @property
    def has_messages(self) -> bool:
        return bool(self.messages)

    @property
    def error_count(self) -> int:
        return sum(1 for m in self.messages if m.is_error)

    @property
    def warning_count(self) -> int:
        return sum(1 for m in self.messages if m.is_warning)

    @property
    def information_count(self) -> int:
        return sum(1 for m in self.messages if m.is_information)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RegistryValidationResult":
        return cls(
            valid=bool(data.get("valid", False)),
            messages=tuple(
                RegistryValidationMessage.from_dict(m)
                for m in data.get("messages", [])
            ),
            metadata=data.get("metadata", {}),
        )


__all__ = ["RegistryValidationResult"]
