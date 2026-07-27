"""
============================================================
Nexa Provider Platform
File: registries/validators/validation_result.py
Layer: Master Registry Foundation
Milestone: NPP-M008.9 — Registry Validation
============================================================

Immutable aggregate result for one deterministic validation run.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .validation_message import RegistryValidationMessage


@dataclass(frozen=True, slots=True)
class RegistryValidationResult:
    """Immutable result returned by registry validators."""

    valid: bool
    messages: tuple[RegistryValidationMessage, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.valid, bool):
            raise TypeError("valid must be a boolean.")

        normalized_messages = tuple(self.messages)
        if not all(isinstance(item, RegistryValidationMessage) for item in normalized_messages):
            raise TypeError("messages must contain RegistryValidationMessage values.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        has_errors = any(message.is_error for message in normalized_messages)
        if self.valid is has_errors:
            raise ValueError(
                "valid must be False when errors exist and True when no errors exist."
            )

        object.__setattr__(self, "messages", normalized_messages)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def is_valid(self) -> bool:
        return self.valid

    @property
    def invalid(self) -> bool:
        return not self.valid

    @property
    def has_messages(self) -> bool:
        return bool(self.messages)

    @property
    def errors(self) -> tuple[RegistryValidationMessage, ...]:
        return tuple(message for message in self.messages if message.is_error)

    @property
    def warnings(self) -> tuple[RegistryValidationMessage, ...]:
        return tuple(message for message in self.messages if message.is_warning)

    @property
    def information(self) -> tuple[RegistryValidationMessage, ...]:
        return tuple(message for message in self.messages if message.is_information)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def information_count(self) -> int:
        return len(self.information)

    @property
    def summary(self) -> str:
        state = "valid" if self.valid else "invalid"
        return (
            f"Registry validation {state}: {self.error_count} error(s), "
            f"{self.warning_count} warning(s), "
            f"{self.information_count} information message(s)."
        )

    def messages_for(self, field: str) -> tuple[RegistryValidationMessage, ...]:
        if not isinstance(field, str):
            raise TypeError("field must be text.")
        normalized = field.strip()
        if not normalized:
            raise ValueError("field cannot be empty.")
        return tuple(message for message in self.messages if message.field == normalized)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "messages": [message.to_dict() for message in self.messages],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RegistryValidationResult":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        raw_messages = data.get("messages", ())
        if isinstance(raw_messages, (str, bytes)) or not isinstance(raw_messages, (list, tuple)):
            raise TypeError("messages must be a list or tuple.")
        messages = tuple(RegistryValidationMessage.from_dict(item) for item in raw_messages)
        valid = data.get("valid")
        if not isinstance(valid, bool):
            raise TypeError("valid must be a boolean.")
        return cls(valid=valid, messages=messages, metadata=data.get("metadata", {}))


__all__ = ["RegistryValidationResult"]
