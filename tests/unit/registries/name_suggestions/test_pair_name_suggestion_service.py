import pytest
from registries.name_suggestions.pair_name_suggestion import PairNameSuggestion
from registries.name_suggestions.pair_name_suggestion_service import PairNameSuggestionService
from registries.name_suggestions.suggestion_errors import NameSuggestionCandidateNotFoundError
from registries.names import FirstName,Surname,MemoryNameRepository

def test_suggests_first_name_and_surname():
    repo=MemoryNameRepository(); repo.add(FirstName('name:first:t','Tariro').as_canonical()); repo.add(Surname('name:surname:n','Ncube').as_canonical())
    result=PairNameSuggestionService(repo).suggest(PairNameSuggestion())
    assert result.rendered_value=='Tariro Ncube'; assert result.component_count==2

def test_pair_is_atomic_when_surname_missing():
    repo=MemoryNameRepository(); repo.add(FirstName('name:first:t','Tariro').as_canonical())
    with pytest.raises(NameSuggestionCandidateNotFoundError): PairNameSuggestionService(repo).suggest(PairNameSuggestion())
