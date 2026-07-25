from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType
import pytest

from registries.contracts.registry_contract import RegistryContract
from registries.core.base_registry import (
    BASE_REGISTRY_SCHEMA_VERSION,
    BaseRegistry,
    BaseRegistryError,
)
from registries.core.registry_definition import RegistryDefinition
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus


def make_definition(
    *,
    status: RegistryStatus = RegistryStatus.ACTIVE,
) -> RegistryDefinition:
    return RegistryDefinition(
        registry_id="registry-person",
        registry_code="person",
        registry_name="Person Registry",
        family=RegistryFamily.CORE_INFRASTRUCTURE,
        status=status,
        description="Canonical person registry.",
        version=2,
        metadata={"owner": "Nexa Provider Platform"},
    )


def test_schema_version_is_stable() -> None:
    assert BASE_REGISTRY_SCHEMA_VERSION == 1


def test_constructs_from_registry_definition() -> None:
    definition = make_definition()
    registry = BaseRegistry(definition)
    assert registry.definition is definition


def test_rejects_non_contract_definition() -> None:
    with pytest.raises(
        BaseRegistryError,
        match="definition must satisfy RegistryContract",
    ):
        BaseRegistry(object())  # type: ignore[arg-type]


def test_satisfies_existing_registry_contract() -> None:
    registry = BaseRegistry(make_definition())
    assert isinstance(registry, RegistryContract)
    assert RegistryContract.require(registry) is registry


def test_delegates_definition_fields() -> None:
    definition = make_definition()
    registry = BaseRegistry(definition)
    assert registry.registry_id == definition.registry_id
    assert registry.registry_code == definition.registry_code
    assert registry.registry_name == definition.registry_name
    assert registry.family is definition.family
    assert registry.status is definition.status
    assert registry.description == definition.description
    assert registry.version == definition.version
    assert registry.metadata is definition.metadata


def test_identity_and_qualified_code_are_deterministic() -> None:
    registry = BaseRegistry(make_definition())
    assert registry.identity == ("registry-person", "PERSON")
    assert registry.qualified_code == "core_infrastructure:PERSON"


@pytest.mark.parametrize(
    ("status", "active", "inactive"),
    [
        (RegistryStatus.DRAFT, False, True),
        (RegistryStatus.ACTIVE, True, False),
        (RegistryStatus.SUSPENDED, False, True),
        (RegistryStatus.RETIRED, False, True),
    ],
)
def test_status_helpers(
    status: RegistryStatus,
    active: bool,
    inactive: bool,
) -> None:
    registry = BaseRegistry(make_definition(status=status))
    assert registry.active is active
    assert registry.inactive is inactive


def test_metadata_helpers_normalize_keys() -> None:
    registry = BaseRegistry(make_definition())
    assert registry.has_metadata(" owner ") is True
    assert registry.metadata_value(" owner ") == "Nexa Provider Platform"
    assert registry.metadata_value("missing", "fallback") == "fallback"


def test_metadata_helpers_reject_invalid_keys() -> None:
    registry = BaseRegistry(make_definition())
    with pytest.raises(TypeError, match="key must be text"):
        registry.has_metadata(123)  # type: ignore[arg-type]
    assert registry.has_metadata("   ") is False
    with pytest.raises(BaseRegistryError, match="key cannot be empty"):
        registry.metadata_value("   ")


def test_metadata_remains_read_only() -> None:
    registry = BaseRegistry(make_definition())
    assert isinstance(registry.metadata, MappingProxyType)
    with pytest.raises(TypeError):
        registry.metadata["owner"] = "changed"  # type: ignore[index]


def test_base_registry_is_frozen() -> None:
    registry = BaseRegistry(make_definition())
    with pytest.raises(FrozenInstanceError):
        registry.definition = make_definition()  # type: ignore[misc]


def test_to_dict_matches_definition_shape() -> None:
    definition = make_definition()
    registry = BaseRegistry(definition)
    assert registry.to_dict() == definition.to_dict()


def test_from_dict_round_trip() -> None:
    original = BaseRegistry(make_definition())
    restored = BaseRegistry.from_dict(original.to_dict())
    assert restored == original
    assert isinstance(restored.definition, RegistryDefinition)


def test_from_dict_requires_mapping() -> None:
    with pytest.raises(TypeError, match="values must be a mapping"):
        BaseRegistry.from_dict([])  # type: ignore[arg-type]


def test_from_definition_is_explicit_constructor() -> None:
    definition = make_definition()
    registry = BaseRegistry.from_definition(definition)
    assert registry.definition is definition


def test_summary_contains_core_identity() -> None:
    summary = BaseRegistry(make_definition()).summary()
    assert "Base Registry" in summary
    assert "registry-person" in summary
    assert "PERSON" in summary
    assert "active" in summary
