import pytest
from registries.name_suggestions.first_eligible_selection_policy import FirstEligibleSelectionPolicy
from registries.name_suggestions.suggestion_errors import NameSuggestionCandidateNotFoundError
from registries.names import FirstName

def test_selects_first_candidate():
    a=FirstName('name:first:a','A').as_canonical(); b=FirstName('name:first:b','B').as_canonical()
    assert FirstEligibleSelectionPolicy().select((a,b)) is a

def test_rejects_empty_candidates():
    with pytest.raises(NameSuggestionCandidateNotFoundError): FirstEligibleSelectionPolicy().select(())
