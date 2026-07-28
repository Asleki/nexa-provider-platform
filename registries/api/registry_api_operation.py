"""Stable operation names exposed by M008.11 Registry API."""
from __future__ import annotations

from enum import Enum

from .registry_api_errors import RegistryApiValidationError


class RegistryApiOperation(str, Enum):
    REGISTER = "register"
    GET = "get"
    REPLACE = "replace"
    REMOVE = "remove"
    LIST = "list"
    EXISTS = "exists"
    COUNT = "count"
    CHANGE_STATUS = "change_status"

    @classmethod
    def parse(cls, value: "RegistryApiOperation | str") -> "RegistryApiOperation":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise RegistryApiValidationError(
                "operation must be a RegistryApiOperation or string."
            )
        normalized = value.strip().lower()
        if not normalized:
            raise RegistryApiValidationError("operation must not be empty.")
        try:
            return cls(normalized)
        except ValueError as exc:
            raise RegistryApiValidationError(
                f"Unsupported registry API operation: {value!r}."
            ) from exc


__all__ = ["RegistryApiOperation"]
