import pytest
from registries.names.name_sex_usage import NameSexUsage
from registries.names.person_sex import PersonSex
@pytest.mark.parametrize("enum,value",[(NameSexUsage,"unisex"),(PersonSex,"intersex")])
def test_parse(enum,value): assert enum.parse(value.upper()).value==value
def test_invalid():
    with pytest.raises(ValueError): NameSexUsage.parse("x")
