import pytest

from registries.core.registry_family import RegistryFamily


def test_registry_family_members_are_exact_and_stable():
    assert tuple(RegistryFamily) == (
        RegistryFamily.CORE_INFRASTRUCTURE,
        RegistryFamily.NEXA_ECOSYSTEM,
        RegistryFamily.SHARED_INFRASTRUCTURE,
    )
    assert tuple(item.value for item in RegistryFamily) == (
        "core_infrastructure",
        "nexa_ecosystem",
        "shared_infrastructure",
    )


def test_registry_family_is_string_compatible():
    assert RegistryFamily.CORE_INFRASTRUCTURE == "core_infrastructure"
    assert RegistryFamily("nexa_ecosystem") is RegistryFamily.NEXA_ECOSYSTEM


def test_registry_family_values_are_unique():
    values = tuple(item.value for item in RegistryFamily)
    assert len(values) == len(set(values))


def test_unknown_registry_family_is_rejected():
    with pytest.raises(ValueError):
        RegistryFamily("citizen")
