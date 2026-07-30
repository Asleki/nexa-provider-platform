"""Request contract for M009.2.3 first-name and surname suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from .suggestion_support import normalize_runtime_mode

@dataclass(frozen=True, slots=True)
class PairNameSuggestion:
    runtime_mode: str = "simulation"
    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime_mode", normalize_runtime_mode(self.runtime_mode))

__all__ = ["PairNameSuggestion"]
