"""Unified structured result for M009.2.5 full-name suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from registries.names import CanonicalName, NameKind
from .full_name_composition import FullNameComposition
from .suggestion_support import validate_component

@dataclass(frozen=True, slots=True)
class FullNameSuggestionResult:
    composition: FullNameComposition
    first_name: CanonicalName
    middle_name: CanonicalName|None=None
    surname: CanonicalName|None=None
    def __post_init__(self)->None:
        object.__setattr__(self,"composition",FullNameComposition.parse(self.composition))
        validate_component(self.first_name,NameKind.FIRST_NAME,"first_name")
        if self.middle_name is not None: validate_component(self.middle_name,NameKind.MIDDLE_NAME,"middle_name")
        if self.surname is not None: validate_component(self.surname,NameKind.SURNAME,"surname")
        expected={
            FullNameComposition.SINGLE_FIRST:(False,False),
            FullNameComposition.FIRST_SURNAME:(False,True),
            FullNameComposition.FIRST_MIDDLE_SURNAME:(True,True),
        }[self.composition]
        if (self.middle_name is not None,self.surname is not None)!=expected:
            raise ValueError("components do not match the requested full-name composition.")
        if len({x.metadata.runtime_mode for x in self.components})!=1:
            raise ValueError("all suggested components must use the same runtime_mode.")
    @property
    def components(self): return tuple(x for x in (self.first_name,self.middle_name,self.surname) if x is not None)
    @property
    def component_ids(self): return tuple(x.name_id for x in self.components)
    @property
    def component_count(self): return len(self.components)
    @property
    def rendered_value(self): return " ".join(x.canonical_value for x in self.components)
    @property
    def runtime_mode(self): return self.first_name.metadata.runtime_mode

__all__=["FullNameSuggestionResult"]
