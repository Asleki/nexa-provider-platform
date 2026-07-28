"""Canonical source types for registry provenance."""
from enum import Enum
class RegistryProvenanceSourceType(str, Enum):
    HUMAN = "human"
    INSTITUTION = "institution"
    SYSTEM = "system"
    IMPORT = "import"
    SIMULATION_GENERATOR = "simulation_generator"
    DERIVED = "derived"
    @classmethod
    def from_value(cls, value):
        if isinstance(value, cls): return value
        if not isinstance(value, str): raise TypeError("provenance source type must be text or RegistryProvenanceSourceType.")
        normalized = value.strip().lower()
        if not normalized: raise ValueError("provenance source type cannot be empty.")
        try: return cls(normalized)
        except ValueError as exc: raise ValueError(f"Unsupported provenance source type {value!r}.") from exc
    def __str__(self): return self.value
__all__ = ["RegistryProvenanceSourceType"]
