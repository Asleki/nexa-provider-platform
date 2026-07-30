"""Result contract for M009.2.2 single-name suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from registries.names import CanonicalName

@dataclass(frozen=True, slots=True)
class SingleNameSuggestionResult:
    name: CanonicalName

    def __post_init__(self) -> None:
        if not isinstance(self.name, CanonicalName):
            raise TypeError("name must be CanonicalName.")

    @property
    def components(self) -> tuple[CanonicalName, ...]: return (self.name,)
    @property
    def component_ids(self) -> tuple[str, ...]: return (self.name.name_id,)
    @property
    def component_count(self) -> int: return 1
    @property
    def rendered_value(self) -> str: return self.name.canonical_value
    @property
    def runtime_mode(self) -> str: return self.name.metadata.runtime_mode

__all__ = ["SingleNameSuggestionResult"]
