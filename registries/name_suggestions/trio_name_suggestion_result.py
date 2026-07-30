"""Result contract for M009.2.4 trio suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from registries.names import CanonicalName, NameKind
from .suggestion_support import validate_component

@dataclass(frozen=True, slots=True)
class TrioNameSuggestionResult:
    first_name: CanonicalName
    middle_name: CanonicalName
    surname: CanonicalName
    def __post_init__(self) -> None:
        validate_component(self.first_name,NameKind.FIRST_NAME,"first_name")
        validate_component(self.middle_name,NameKind.MIDDLE_NAME,"middle_name")
        validate_component(self.surname,NameKind.SURNAME,"surname")
        if len({x.metadata.runtime_mode for x in self.components}) != 1:
            raise ValueError("all suggested components must use the same runtime_mode.")
    @property
    def components(self): return (self.first_name,self.middle_name,self.surname)
    @property
    def component_ids(self): return tuple(x.name_id for x in self.components)
    @property
    def component_count(self): return 3
    @property
    def rendered_value(self): return " ".join(x.canonical_value for x in self.components)
    @property
    def runtime_mode(self): return self.first_name.metadata.runtime_mode

__all__=["TrioNameSuggestionResult"]
