from registries import core
from registries.core.base_registry import (
    BASE_REGISTRY_SCHEMA_VERSION,
    BaseRegistry,
    BaseRegistryError,
)


def test_base_registry_exports_are_public() -> None:
    assert core.BASE_REGISTRY_SCHEMA_VERSION is BASE_REGISTRY_SCHEMA_VERSION
    assert core.BaseRegistry is BaseRegistry
    assert core.BaseRegistryError is BaseRegistryError


def test_existing_exports_remain_available() -> None:
    expected = {
        "RegistryFamily",
        "RegistryStatus",
        "RegistryDefinition",
        "RegistryDefinitionError",
        "IdentifierLifecycle",
        "NamespaceDefinition",
        "IdentifierDefinition",
        "NumberingMode",
        "NumberingStrategy",
        "IdentifierReference",
    }
    assert expected.issubset(set(core.__all__))
