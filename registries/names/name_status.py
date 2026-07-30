"""Lifecycle status for canonical name catalogue records."""
from __future__ import annotations
from enum import Enum

class NameStatus(str, Enum):
    ACTIVE="active"
    INACTIVE="inactive"
    DEPRECATED="deprecated"

    @classmethod
    def parse(cls, value: object) -> "NameStatus":
        if isinstance(value, cls): return value
        if not isinstance(value, str): raise TypeError("status must be text or NameStatus.")
        try: return cls(value.strip().lower())
        except ValueError as exc: raise ValueError(f"unsupported name status: {value!r}.") from exc

__all__=["NameStatus"]
