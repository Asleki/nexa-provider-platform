import pytest
from registries.name_suggestions.single_name_suggestion import SingleNameSuggestion
from registries.names import NameKind

def test_normalizes_request():
    r=SingleNameSuggestion('surname',' Production ')
    assert r.name_kind is NameKind.SURNAME and r.runtime_mode=='production'

def test_rejects_empty_runtime():
    with pytest.raises(ValueError): SingleNameSuggestion(NameKind.FIRST_NAME,' ')
