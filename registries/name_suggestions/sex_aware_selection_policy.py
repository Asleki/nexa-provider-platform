"""Selection policy that prefers compatible canonical names."""
from __future__ import annotations
from registries.names import CanonicalName
from registries.names.person_sex import PersonSex
from .name_sex_compatibility import evaluate_name_sex_compatibility
from .name_sex_compatibility_outcome import NameSexCompatibilityOutcome as O
from .suggestion_errors import NameSuggestionCandidateNotFoundError
from .suggestion_selection_policy import SuggestionSelectionPolicy
class SexAwareSelectionPolicy(SuggestionSelectionPolicy):
    def __init__(self,person_sex:PersonSex|str,*,allow_unspecified:bool=True,allow_ambiguous:bool=True)->None:
        self._person_sex=PersonSex.parse(person_sex); self._allow_unspecified=bool(allow_unspecified); self._allow_ambiguous=bool(allow_ambiguous)
    def select(self,candidates:tuple[CanonicalName,...])->CanonicalName:
        if not isinstance(candidates,tuple) or any(not isinstance(c,CanonicalName) for c in candidates): raise TypeError("candidates must be a tuple of CanonicalName records.")
        accepted={O.COMPATIBLE}
        if self._allow_ambiguous: accepted.add(O.AMBIGUOUS)
        if self._allow_unspecified: accepted.add(O.UNSPECIFIED)
        for candidate in candidates:
            if evaluate_name_sex_compatibility(self._person_sex,candidate).outcome in accepted: return candidate
        raise NameSuggestionCandidateNotFoundError("no sex-compatible canonical name candidate was found.")
__all__=["SexAwareSelectionPolicy"]
