import pytest
from registries.names import CanonicalName,NameKind

def test_canonical_name_is_immutable_normalized_and_serializable():
    n=CanonicalName("name:first:1","  José   María ",NameKind.FIRST_NAME)
    assert n.canonical_value=="José María"
    assert n.search_value=="josé maría"
    assert n.identity_key==("simulation","first_name","josé maría")
    assert CanonicalName.from_dict(n.to_dict())==n
    with pytest.raises(Exception): n.name_id="other"

def test_canonical_name_rejects_invalid_values():
    with pytest.raises(ValueError): CanonicalName("bad id","Alex",NameKind.FIRST_NAME)
    with pytest.raises(ValueError): CanonicalName("id", "   ",NameKind.FIRST_NAME)
