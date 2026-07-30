import pytest
from registries.names import FirstName,NameKind

def test_first_name_enforces_kind_and_round_trip():
    n=FirstName("first:1"," Tariro ")
    assert n.name_kind is NameKind.FIRST_NAME
    assert FirstName.from_dict(n.to_dict())==n

def test_first_name_rejects_other_kind_mapping():
    d=FirstName("first:1","Tariro").to_dict(); d["name_kind"]="surname"
    with pytest.raises(ValueError): FirstName.from_dict(d)
