from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from registries.contracts import RegistryContract
from registries.core.registry_definition import (
    DEFAULT_REGISTRY_DEFINITION_VERSION,
    RegistryDefinition,
    RegistryDefinitionError,
)
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus


def _definition(**overrides):
    values = {
        "registry_id": " npp.registry.providers ",
        "registry_code": " providers ",
        "registry_name": " Provider Registry ",
        "family": RegistryFamily.CORE_INFRASTRUCTURE,
        "status": RegistryStatus.ACTIVE,
        "description": " Canonical registry. ",
        "version": 1,
        "metadata": {"owner": "platform"},
    }
    values.update(overrides)
    return RegistryDefinition(**values)


def test_valid_construction_normalizes_values():
    definition = _definition()
    assert definition.registry_id == "npp.registry.providers"
    assert definition.registry_code == "PROVIDERS"
    assert definition.registry_name == "Provider Registry"
    assert definition.description == "Canonical registry."
    assert definition.version == DEFAULT_REGISTRY_DEFINITION_VERSION
    assert definition.active is True
    assert definition.inactive is False
    assert definition.identity == ("npp.registry.providers", "PROVIDERS")
    assert definition.qualified_code == "core_infrastructure:PROVIDERS"
    assert isinstance(definition, RegistryContract)


@pytest.mark.parametrize("field", ["registry_id", "registry_code", "registry_name"])
def test_required_text_rejects_blank_values(field):
    with pytest.raises(RegistryDefinitionError, match=f"{field} cannot be empty"):
        _definition(**{field: "   "})


@pytest.mark.parametrize("field", ["registry_id", "registry_code", "registry_name"])
def test_required_text_rejects_non_text(field):
    with pytest.raises(TypeError, match=f"{field} must be text"):
        _definition(**{field: 123})


def test_enum_values_may_be_constructed_from_stable_strings():
    definition = _definition(
        family="nexa_ecosystem",
        status="suspended",
    )
    assert definition.family is RegistryFamily.NEXA_ECOSYSTEM
    assert definition.status is RegistryStatus.SUSPENDED


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("family", "unknown", "Unsupported registry family"),
        ("status", "unknown", "Unsupported registry status"),
    ],
)
def test_unknown_enum_values_are_rejected(field, value, message):
    with pytest.raises(RegistryDefinitionError, match=message):
        _definition(**{field: value})


@pytest.mark.parametrize("version", [True, False, 1.5, "1", None])
def test_version_rejects_non_integer_values(version):
    with pytest.raises(TypeError, match="version must be an integer"):
        _definition(version=version)


def test_version_rejects_values_below_one():
    with pytest.raises(RegistryDefinitionError, match="greater than or equal to 1"):
        _definition(version=0)


def test_description_must_be_text():
    with pytest.raises(TypeError, match="description must be text"):
        _definition(description=None)


def test_metadata_is_defensively_copied_and_read_only():
    source = {"owner": "platform"}
    definition = _definition(metadata=source)
    source["owner"] = "changed"

    assert definition.metadata == {"owner": "platform"}
    assert isinstance(definition.metadata, MappingProxyType)
    with pytest.raises(TypeError):
        definition.metadata["owner"] = "changed"


@pytest.mark.parametrize("metadata", [None, [], "metadata"])
def test_metadata_must_be_a_mapping(metadata):
    with pytest.raises(TypeError, match="metadata must be a mapping"):
        _definition(metadata=metadata)


def test_metadata_keys_must_be_non_empty_text():
    with pytest.raises(TypeError, match="metadata keys must be text"):
        _definition(metadata={1: "value"})
    with pytest.raises(RegistryDefinitionError, match="metadata keys cannot be empty"):
        _definition(metadata={"   ": "value"})


def test_frozen_definition_rejects_assignment():
    definition = _definition()
    with pytest.raises(FrozenInstanceError):
        definition.registry_name = "Changed"


def test_serialization_and_round_trip_are_deterministic():
    definition = _definition()
    serialized = definition.to_dict()
    rebuilt = RegistryDefinition.from_dict(serialized)

    assert serialized == {
        "registry_id": "npp.registry.providers",
        "registry_code": "PROVIDERS",
        "registry_name": "Provider Registry",
        "family": "core_infrastructure",
        "status": "active",
        "description": "Canonical registry.",
        "version": 1,
        "metadata": {"owner": "platform"},
    }
    assert rebuilt == definition


def test_from_dict_rejects_non_mapping_and_unknown_fields():
    with pytest.raises(TypeError, match="values must be a mapping"):
        RegistryDefinition.from_dict([])
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        RegistryDefinition.from_dict(
            {
                **_definition().to_dict(),
                "unknown": True,
            }
        )


def test_source_mapping_is_not_mutated_by_from_dict():
    source = _definition().to_dict()
    before = dict(source)
    RegistryDefinition.from_dict(source)
    assert source == before


def test_metadata_access_helpers():
    definition = _definition()
    assert definition.has_metadata(" owner ") is True
    assert definition.has_metadata("missing") is False
    assert definition.has_metadata("  ") is False
    assert definition.metadata_value(" owner ") == "platform"
    assert definition.metadata_value("missing", "fallback") == "fallback"
    with pytest.raises(TypeError, match="key must be text"):
        definition.metadata_value(1)
    with pytest.raises(ValueError, match="key cannot be empty"):
        definition.metadata_value("   ")


def test_summary_contains_stable_identity_fields():
    summary = _definition().summary()
    assert "npp.registry.providers" in summary
    assert "PROVIDERS" in summary
    assert "Provider Registry" in summary
    assert "core_infrastructure" in summary
    assert "active" in summary
