"""Request contract for M009.2.5 full-name suggestions."""
from __future__ import annotations
from dataclasses import dataclass
from .full_name_composition import FullNameComposition
from .suggestion_support import normalize_runtime_mode

@dataclass(frozen=True, slots=True)
class FullNameSuggestion:
    composition: FullNameComposition=FullNameComposition.FIRST_MIDDLE_SURNAME
    runtime_mode: str="simulation"
    def __post_init__(self)->None:
        object.__setattr__(self,"composition",FullNameComposition.parse(self.composition))
        object.__setattr__(self,"runtime_mode",normalize_runtime_mode(self.runtime_mode))

__all__=["FullNameSuggestion"]
