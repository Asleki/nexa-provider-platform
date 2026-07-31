"""Aggregate component-level name/sex compatibility."""
from __future__ import annotations
from dataclasses import dataclass
from registries.names import CanonicalName
from registries.names.person_sex import PersonSex
from .name_sex_compatibility import evaluate_name_sex_compatibility
from .name_sex_compatibility_outcome import NameSexCompatibilityOutcome as O
from .name_sex_compatibility_result import NameSexCompatibilityResult
@dataclass(frozen=True,slots=True)
class FullNameSexCompatibilityResult:
    person_sex:PersonSex
    outcome:O
    components:tuple[NameSexCompatibilityResult,...]
    def __post_init__(self):
        object.__setattr__(self,"person_sex",PersonSex.parse(self.person_sex)); object.__setattr__(self,"components",tuple(self.components))
        if not isinstance(self.outcome,O): object.__setattr__(self,"outcome",O(self.outcome))

def evaluate_full_name_sex_compatibility(person_sex:PersonSex|str,names:tuple[CanonicalName,...])->FullNameSexCompatibilityResult:
    if not isinstance(names,tuple) or any(not isinstance(n,CanonicalName) for n in names): raise TypeError("names must be a tuple of CanonicalName records.")
    sex=PersonSex.parse(person_sex); parts=tuple(evaluate_name_sex_compatibility(sex,n) for n in names); outcomes={p.outcome for p in parts}
    if O.CONFLICT in outcomes: outcome=O.CONFLICT
    elif O.COMPATIBLE in outcomes: outcome=O.COMPATIBLE
    elif O.AMBIGUOUS in outcomes: outcome=O.AMBIGUOUS
    else: outcome=O.UNSPECIFIED
    return FullNameSexCompatibilityResult(sex,outcome,parts)
__all__=["FullNameSexCompatibilityResult","evaluate_full_name_sex_compatibility"]
