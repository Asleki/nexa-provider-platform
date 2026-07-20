
"""
registries.validators.validation_collector

Mutable helper used to collect validation messages and produce an immutable
RegistryValidationResult.
"""

from __future__ import annotations

from typing import Iterable, List

from .validation_message import RegistryValidationMessage
from .validation_result import RegistryValidationResult


class RegistryValidationCollector:
    """Collects validation messages during validation."""

    __slots__ = ("_messages",)

    def __init__(self) -> None:
        self._messages: List[RegistryValidationMessage] = []

    def add(self, message: RegistryValidationMessage) -> None:
        self._messages.append(message)

    def extend(self, messages: Iterable[RegistryValidationMessage]) -> None:
        self._messages.extend(messages)

    @property
    def messages(self) -> tuple[RegistryValidationMessage, ...]:
        return tuple(self._messages)

    @property
    def has_errors(self) -> bool:
        return any(m.is_error for m in self._messages)

    @property
    def has_warnings(self) -> bool:
        return any(m.is_warning for m in self._messages)

    @property
    def is_empty(self) -> bool:
        return not self._messages

    def clear(self) -> None:
        self._messages.clear()

    def build(self) -> RegistryValidationResult:
        return RegistryValidationResult(
            valid=not self.has_errors,
            messages=self.messages,
        )


__all__ = ["RegistryValidationCollector"]
