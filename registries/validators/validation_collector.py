"""
============================================================
Nexa Provider Platform
File: registries/validators/validation_collector.py
Layer: Master Registry Foundation
Milestone: NPP-M008.9 — Registry Validation
============================================================

Internal mutable collector that emits immutable validation results.
============================================================
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .validation_message import RegistryValidationMessage
from .validation_result import RegistryValidationResult


class RegistryValidationCollector:
    """Collect validation findings during one validation run."""

    __slots__ = ("_messages",)

    def __init__(self) -> None:
        self._messages: list[RegistryValidationMessage] = []

    def add(self, message: RegistryValidationMessage) -> None:
        if not isinstance(message, RegistryValidationMessage):
            raise TypeError("message must be a RegistryValidationMessage.")
        self._messages.append(message)

    def extend(self, messages: Iterable[RegistryValidationMessage]) -> None:
        if isinstance(messages, (str, bytes)):
            raise TypeError("messages must be an iterable of validation messages.")
        for message in messages:
            self.add(message)

    @property
    def messages(self) -> tuple[RegistryValidationMessage, ...]:
        return tuple(self._messages)

    @property
    def has_errors(self) -> bool:
        return any(message.is_error for message in self._messages)

    @property
    def has_warnings(self) -> bool:
        return any(message.is_warning for message in self._messages)

    @property
    def is_empty(self) -> bool:
        return not self._messages

    def clear(self) -> None:
        self._messages.clear()

    def build(self, *, metadata: Mapping[str, object] | None = None) -> RegistryValidationResult:
        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping or None.")
        return RegistryValidationResult(
            valid=not self.has_errors,
            messages=self.messages,
            metadata={} if metadata is None else metadata,
        )


__all__ = ["RegistryValidationCollector"]
