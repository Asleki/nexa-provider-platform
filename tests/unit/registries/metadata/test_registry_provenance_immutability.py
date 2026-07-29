from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from registries.metadata import RegistryProvenance, RegistryProvenanceError

NOW = datetime(2026, 7, 29, tzinfo=timezone.utc)


def make(attributes):
    return RegistryProvenance("system", "npp", recorded_at=NOW, attributes=attributes)


def test_dataclass_fields_cannot_be_reassigned():
    item = make({})
    with pytest.raises(FrozenInstanceError):
        item.source_system = "changed"


def test_nested_attribute_values_are_recursively_immutable():
    item = make({"nested": {"items": ["a", "b"], "tags": {"x", "y"}}})
    assert isinstance(item.attributes, MappingProxyType)
    assert isinstance(item.attributes["nested"], MappingProxyType)
    assert item.attributes["nested"]["items"] == ("a", "b")
    assert item.attributes["nested"]["tags"] == frozenset({"x", "y"})
    with pytest.raises(TypeError):
        item.attributes["nested"]["new"] = True


def test_caller_mutation_cannot_change_existing_provenance():
    values = {"nested": {"items": ["a"]}}
    item = make(values)
    values["nested"]["items"].append("b")
    assert item.attributes["nested"]["items"] == ("a",)


def test_attribute_keys_are_trimmed_and_remain_unique():
    item = make({" source ": "value"})
    assert item.attributes == {"source": "value"}

    with pytest.raises(RegistryProvenanceError, match="cannot be empty"):
        make({"   ": "value"})
    with pytest.raises(RegistryProvenanceError, match="remain unique"):
        make({"a": 1, " a ": 2})


def test_attribute_keys_must_be_text_and_nested_mapping_keys_hashable():
    with pytest.raises(TypeError, match="attribute keys must be text"):
        make({1: "value"})
