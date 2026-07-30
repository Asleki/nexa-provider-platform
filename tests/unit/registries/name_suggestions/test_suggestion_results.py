import pytest
from registries.name_suggestions.pair_name_suggestion_result import PairNameSuggestionResult
from registries.name_suggestions.trio_name_suggestion_result import TrioNameSuggestionResult
from registries.names import FirstName,MiddleName,Surname,NameMetadata

def test_pair_rejects_mixed_runtime_modes():
    first=FirstName('name:first:a','A').as_canonical(); surname=Surname('name:surname:b','B',NameMetadata(runtime_mode='production')).as_canonical()
    with pytest.raises(ValueError,match='same runtime_mode'): PairNameSuggestionResult(first,surname)

def test_trio_requires_correct_kinds():
    first=FirstName('name:first:a','A').as_canonical(); middle=MiddleName('name:middle:b','B').as_canonical(); surname=Surname('name:surname:c','C').as_canonical()
    assert TrioNameSuggestionResult(first,middle,surname).component_count==3
    with pytest.raises(ValueError): TrioNameSuggestionResult(first,surname,middle)
