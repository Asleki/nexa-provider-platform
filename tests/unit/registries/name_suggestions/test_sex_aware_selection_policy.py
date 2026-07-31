import pytest
from registries.names import CanonicalName,NameKind,NameMetadata
from registries.names.name_sex_usage_metadata import with_name_sex_usage
from registries.name_suggestions.sex_aware_selection_policy import SexAwareSelectionPolicy
from registries.name_suggestions.suggestion_errors import NameSuggestionCandidateNotFoundError
def n(i,u): return CanonicalName(i,i,NameKind.FIRST_NAME,with_name_sex_usage(NameMetadata(),u))
def test_skips_conflict_and_preserves_order(): assert SexAwareSelectionPolicy("male").select((n("Grace","female"),n("Alex","unisex"),n("John","male"))).name_id=="Alex"
def test_strict_policy_can_reject_unspecified():
    with pytest.raises(NameSuggestionCandidateNotFoundError): SexAwareSelectionPolicy("male",allow_unspecified=False).select((n("Unknown","unspecified"),))
