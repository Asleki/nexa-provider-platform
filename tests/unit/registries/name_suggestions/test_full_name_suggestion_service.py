import pytest
from registries.name_suggestions.full_name_composition import FullNameComposition
from registries.name_suggestions.full_name_suggestion import FullNameSuggestion
from registries.name_suggestions.full_name_suggestion_service import FullNameSuggestionService
from registries.name_suggestions.full_name_suggestion_result import FullNameSuggestionResult
from registries.names import FirstName,MiddleName,Surname,MemoryNameRepository

def _repo():
    repo=MemoryNameRepository(); repo.add(FirstName('name:first:t','Tariro').as_canonical()); repo.add(MiddleName('name:middle:r','Rudo').as_canonical()); repo.add(Surname('name:surname:n','Ncube').as_canonical()); return repo

@pytest.mark.parametrize(('shape','text','count'),[(FullNameComposition.SINGLE_FIRST,'Tariro',1),(FullNameComposition.FIRST_SURNAME,'Tariro Ncube',2),(FullNameComposition.FIRST_MIDDLE_SURNAME,'Tariro Rudo Ncube',3)])
def test_orchestrates_supported_compositions(shape,text,count):
    result=FullNameSuggestionService(_repo()).suggest(FullNameSuggestion(shape))
    assert result.rendered_value==text and result.component_count==count

def test_result_rejects_components_not_matching_shape():
    repo=_repo(); first=repo.get('name:first:t'); middle=repo.get('name:middle:r'); surname=repo.get('name:surname:n')
    with pytest.raises(ValueError,match='do not match'):
        FullNameSuggestionResult(FullNameComposition.FIRST_SURNAME,first,middle,surname)
