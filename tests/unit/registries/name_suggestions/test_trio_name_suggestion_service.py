from registries.name_suggestions.trio_name_suggestion import TrioNameSuggestion
from registries.name_suggestions.trio_name_suggestion_service import TrioNameSuggestionService
from registries.names import FirstName,MiddleName,Surname,MemoryNameRepository

def test_suggests_structured_trio():
    repo=MemoryNameRepository(); repo.add(FirstName('name:first:t','Tariro').as_canonical()); repo.add(MiddleName('name:middle:r','Rudo').as_canonical()); repo.add(Surname('name:surname:n','Ncube').as_canonical())
    result=TrioNameSuggestionService(repo).suggest(TrioNameSuggestion())
    assert result.rendered_value=='Tariro Rudo Ncube'; assert result.component_ids==('name:first:t','name:middle:r','name:surname:n')
