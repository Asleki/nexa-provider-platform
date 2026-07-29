from types import MappingProxyType

import pytest

from registries.relationships import (
    RegistryReference,
    RegistryReferenceError,
    RelationshipDefinition,
    RelationshipDefinitionError,
    RelationshipType,
    RelationshipTypeError,
)


def test_nested_input_values_are_recursively_frozen_and_detached():
    source_data = {"nested": {"items": [1, 2], "flags": {"a", "b"}}}
    reference = RegistryReference("citizen.registry", "NVG-CIT-1", attributes=source_data)
    source_data["nested"]["items"].append(3)
    assert isinstance(reference.attributes, MappingProxyType)
    assert reference.attributes["nested"]["items"] == (1, 2)
    with pytest.raises(TypeError):
        reference.attributes["nested"]["new"] = True


def test_all_contracts_reject_attribute_key_collisions_after_normalisation():
    with pytest.raises(RegistryReferenceError, match="remain unique"):
        RegistryReference("citizen.registry", "1", attributes={"a": 1, " a ": 2})
    with pytest.raises(RelationshipTypeError, match="remain unique"):
        RelationshipType("type.a", "TYPE.A", "A", attributes={"a": 1, " a ": 2})
    with pytest.raises(RelationshipDefinitionError, match="remain unique"):
        RelationshipDefinition(
            "rel-1",
            RelationshipType("type.a", "TYPE.A", "A"),
            RegistryReference("a.registry", "1"),
            RegistryReference("b.registry", "2"),
            "simulation",
            attributes={"a": 1, " a ": 2},
        )
