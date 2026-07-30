"""Request contract for M009.2.2 single-name suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from registries.names import NameKind
from .suggestion_support import normalize_runtime_mode

@dataclass(frozen=True, slots=True)
class SingleNameSuggestion:
    name_kind: NameKind
    runtime_mode: str = "simulation"

    def __post_init__(self) -> None:
        object.__setattr__(self, "name_kind", NameKind.parse(self.name_kind))
        object.__setattr__(self, "runtime_mode", normalize_runtime_mode(self.runtime_mode))

__all__ = ["SingleNameSuggestion"]
