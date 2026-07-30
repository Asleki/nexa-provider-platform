import pytest
from registries.name_suggestions.single_name_suggestion import SingleNameSuggestion
from registries.name_suggestions.single_name_suggestion_service import SingleNameSuggestionService
from registries.name_suggestions.suggestion_errors import NameSuggestionCandidateNotFoundError
from registries.names import FirstName,MemoryNameRepository,NameKind,NameMetadata

def test_suggests_first_active_runtime_scoped_name_without_mutation():
    repo=MemoryNameRepository(); repo.add(FirstName('name:first:z','Zara').as_canonical()); repo.add(FirstName('name:first:a','Amina').as_canonical())
    repo.add(FirstName('name:first:p','Prod',NameMetadata(runtime_mode='production')).as_canonical()); before=repo.count()
    result=SingleNameSuggestionService(repo).suggest(SingleNameSuggestion(NameKind.FIRST_NAME))
    assert result.rendered_value=='Amina'; assert result.component_ids==('name:first:a',); assert repo.count()==before

def test_fails_when_no_candidate_exists():
    with pytest.raises(NameSuggestionCandidateNotFoundError):
        SingleNameSuggestionService(MemoryNameRepository()).suggest(SingleNameSuggestion(NameKind.SURNAME))
