"""Semantic kinds supported by the M009.1 canonical name catalogue."""
from __future__ import annotations
from enum import Enum

class NameKind(str, Enum):
    FIRST_NAME = "first_name"
    MIDDLE_NAME = "middle_name"
    SURNAME = "surname"

    @classmethod
    def parse(cls, value: object) -> "NameKind":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("name_kind must be text or NameKind.")
        normalized=value.strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"unsupported name_kind: {value!r}.") from exc

__all__=["NameKind"]
