from dataclasses import FrozenInstanceError
from datetime import timedelta
from types import MappingProxyType

import pytest

from registries.metadata import RegistryRetention, RegistryRetentionError


def make(attributes=None):
    return RegistryRetention(
        "fixed_duration",
        "Temporary",
        retention_period=timedelta(days=1),
        attributes={} if attributes is None else attributes,
    )


def test_dataclass_fields_are_frozen():
    item = make()
    with pytest.raises(FrozenInstanceError):
        item.reason = "Changed"


def test_nested_attributes_are_recursively_immutable():
    item = make({"nested": {"list": [1, {"value": 2}], "set": {3, 4}}})
    assert isinstance(item.attributes, MappingProxyType)
    assert isinstance(item.attributes["nested"], MappingProxyType)
    assert isinstance(item.attributes["nested"]["list"], tuple)
    assert isinstance(item.attributes["nested"]["set"], frozenset)
    with pytest.raises(TypeError):
        item.attributes["other"] = 1
    with pytest.raises(TypeError):
        item.attributes["nested"]["other"] = 1


def test_caller_mutation_does_not_change_contract():
    source = {"nested": {"items": [1, 2]}}
    item = make(source)
    source["nested"]["items"].append(3)
    assert item.to_dict()["attributes"] == {"nested": {"items": [1, 2]}}


def test_attribute_keys_are_trimmed_and_must_be_unique():
    item = make({" scope ": "central"})
    assert item.attributes["scope"] == "central"
    with pytest.raises(RegistryRetentionError, match="cannot be empty"):
        make({" ": 1})
    with pytest.raises(RegistryRetentionError, match="remain unique"):
        make({"scope": 1, " scope ": 2})


def test_attribute_keys_must_be_text():
    with pytest.raises(TypeError, match="attribute keys must be text"):
        make({1: "invalid"})


def test_attributes_must_be_a_mapping():
    with pytest.raises(TypeError, match="attributes must be a mapping"):
        make(attributes=[])
