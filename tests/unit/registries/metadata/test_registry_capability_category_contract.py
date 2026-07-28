import pytest

from registries.metadata import RegistryCapabilityCategory


def test_category_contract_remains_broad_and_stable():
    assert tuple(item.value for item in RegistryCapabilityCategory.all()) == (
        "identity",
        "lifecycle",
        "issuance",
        "discovery",
        "validation",
        "import",
        "export",
        "audit",
        "simulation",
    )


def test_category_normalization_accepts_enum_or_text():
    assert RegistryCapabilityCategory.from_value(" SIMULATION ") is RegistryCapabilityCategory.SIMULATION
    assert RegistryCapabilityCategory.from_value(RegistryCapabilityCategory.AUDIT) is RegistryCapabilityCategory.AUDIT


def test_category_rejects_unknown_or_non_text_values():
    with pytest.raises(ValueError):
        RegistryCapabilityCategory.from_value("monetary")
    with pytest.raises(TypeError):
        RegistryCapabilityCategory.from_value(1)
