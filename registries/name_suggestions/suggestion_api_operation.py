"""Supported M009.2.8 suggestion API operations."""
from enum import Enum


class SuggestionApiOperation(str, Enum):
    NORMALIZE = "normalize"
    CHECK_DUPLICATE = "check_duplicate"
    SUGGEST_SINGLE = "suggest_single"
    SUGGEST_PAIR = "suggest_pair"
    SUGGEST_TRIO = "suggest_trio"
    SUGGEST_FULL_NAME = "suggest_full_name"

    @classmethod
    def parse(cls, value: object) -> "SuggestionApiOperation":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("operation must be text or SuggestionApiOperation.")
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            raise ValueError(f"unsupported suggestion API operation: {value!r}.") from exc


__all__ = ["SuggestionApiOperation"]
