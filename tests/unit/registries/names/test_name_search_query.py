import pytest
from registries.names import NameSearchQuery,NameKind,NameStatus

def test_query_normalizes_filters_and_pagination():
    q=NameSearchQuery("  Ta  ","first_name","active"," SIMULATION ",True,10,2)
    assert q.text=="Ta" and q.name_kind is NameKind.FIRST_NAME and q.status is NameStatus.ACTIVE and q.runtime_mode=="simulation"

def test_query_rejects_invalid_pagination():
    with pytest.raises(ValueError): NameSearchQuery(limit=0)
    with pytest.raises(ValueError): NameSearchQuery(offset=-1)
