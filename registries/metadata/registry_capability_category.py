"""Broad categories used to classify registry capabilities."""
from enum import Enum

class RegistryCapabilityCategory(str, Enum):
    IDENTITY = "identity"
    LIFECYCLE = "lifecycle"
    ISSUANCE = "issuance"
    DISCOVERY = "discovery"
    VALIDATION = "validation"
    IMPORT = "import"
    EXPORT = "export"
    AUDIT = "audit"
    SIMULATION = "simulation"

    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls): return value
        if not isinstance(value, str): raise TypeError("capability category must be text or RegistryCapabilityCategory.")
        normalized = value.strip().lower()
        if not normalized: raise ValueError("capability category cannot be empty.")
        try: return cls(normalized)
        except ValueError as exc: raise ValueError(f"Unsupported capability category {value!r}.") from exc

    @classmethod
    def all(cls): return tuple(cls)
    def __str__(self): return self.value

__all__ = ["RegistryCapabilityCategory"]
