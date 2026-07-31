"""Immutable compatibility result."""
from __future__ import annotations
from dataclasses import dataclass
from registries.names.person_sex import PersonSex
from registries.names.name_sex_usage import NameSexUsage
from .name_sex_compatibility_outcome import NameSexCompatibilityOutcome
@dataclass(frozen=True,slots=True)
class NameSexCompatibilityResult:
    person_sex:PersonSex
    name_usage:NameSexUsage
    outcome:NameSexCompatibilityOutcome
    name_id:str|None=None
    def __post_init__(self)->None:
        object.__setattr__(self,"person_sex",PersonSex.parse(self.person_sex)); object.__setattr__(self,"name_usage",NameSexUsage.parse(self.name_usage))
        if not isinstance(self.outcome,NameSexCompatibilityOutcome): object.__setattr__(self,"outcome",NameSexCompatibilityOutcome(self.outcome))
        if self.name_id is not None and (not isinstance(self.name_id,str) or not self.name_id.strip()): raise ValueError("name_id must be non-empty text or None.")
    @property
    def is_eligible(self)->bool: return self.outcome in {NameSexCompatibilityOutcome.COMPATIBLE,NameSexCompatibilityOutcome.AMBIGUOUS,NameSexCompatibilityOutcome.UNSPECIFIED}
__all__=["NameSexCompatibilityResult"]
