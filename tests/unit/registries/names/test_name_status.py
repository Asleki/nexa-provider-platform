import pytest
from registries.names import NameStatus

def test_name_status_values_and_parse():
    assert NameStatus.parse(" Active ") is NameStatus.ACTIVE
    assert {x.value for x in NameStatus}=={"active","inactive","deprecated"}

def test_name_status_rejects_invalid_values():
    with pytest.raises(ValueError): NameStatus.parse("deleted")
