"""Request contract for M009.2.4 trio suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from .suggestion_support import normalize_runtime_mode

@dataclass(frozen=True, slots=True)
class TrioNameSuggestion:
    runtime_mode: str = "simulation"
    def __post_init__(self) -> None:
        object.__setattr__(self,"runtime_mode",normalize_runtime_mode(self.runtime_mode))

__all__=["TrioNameSuggestion"]
