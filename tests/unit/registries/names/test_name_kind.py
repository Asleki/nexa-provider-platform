import pytest
from registries.names import NameKind

def test_name_kind_values_and_parse():
    assert NameKind.parse(" FIRST_NAME ") is NameKind.FIRST_NAME
    assert NameKind.SURNAME.value=="surname"

def test_name_kind_rejects_invalid_values():
    with pytest.raises(ValueError): NameKind.parse("nickname")
    with pytest.raises(TypeError): NameKind.parse(2)
