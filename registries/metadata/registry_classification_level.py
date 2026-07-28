"""Ordered data-classification levels for registry metadata."""
from enum import IntEnum

class RegistryClassificationLevel(IntEnum):
    PUBLIC = 10
    INTERNAL = 20
    RESTRICTED = 30
    CONFIDENTIAL = 40
    HIGHLY_RESTRICTED = 50

    @property
    def code(self): return self.name.lower()
    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls): return value
        if not isinstance(value, str): raise TypeError("classification level must be text or RegistryClassificationLevel.")
        normalized = value.strip().upper()
        if not normalized: raise ValueError("classification level cannot be empty.")
        try: return cls[normalized]
        except KeyError as exc: raise ValueError(f"Unsupported classification level {value!r}.") from exc
    def __str__(self): return self.code

__all__ = ["RegistryClassificationLevel"]
