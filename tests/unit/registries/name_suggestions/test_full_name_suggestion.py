import pytest
from registries.name_suggestions.full_name_composition import FullNameComposition
from registries.name_suggestions.full_name_suggestion import FullNameSuggestion

def test_parses_composition_and_runtime():
    r=FullNameSuggestion('first_surname',' Production ')
    assert r.composition is FullNameComposition.FIRST_SURNAME and r.runtime_mode=='production'

def test_rejects_unknown_composition():
    with pytest.raises(ValueError): FullNameSuggestion('unknown')
