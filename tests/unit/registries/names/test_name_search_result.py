import pytest
from registries.names import CanonicalName,NameKind,NameSearchResult

def test_search_result_is_immutable_tuple_page():
    n=CanonicalName("id:1","Alex",NameKind.FIRST_NAME)
    r=NameSearchResult([n],1,10,0)
    assert r.records==(n,)

def test_search_result_rejects_inconsistent_page():
    with pytest.raises(ValueError): NameSearchResult((),0,10,1)
