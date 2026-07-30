import pytest
from registries.names import MiddleName,NameKind

def test_middle_name_enforces_kind_and_round_trip():
    n=MiddleName("middle:1","Rudo")
    assert n.name_kind is NameKind.MIDDLE_NAME
    assert MiddleName.from_dict(n.to_dict())==n
