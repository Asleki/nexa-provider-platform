from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from registries.metadata import RegistryMetadataProfileError
from tests.unit.registries.metadata.metadata_test_support import make_profile


def test_profile_recursively_detaches_and_freezes_attribute_values():
    source = {"policy_refs": ["policy.v1"], "nested": {"countries": {"KE", "NVG"}}}
    profile = make_profile(attributes=source)
    source["policy_refs"].append("policy.v2")
    source["nested"]["countries"].add("ZW")

    assert isinstance(profile.attributes, MappingProxyType)
    assert profile.attributes["policy_refs"] == ("policy.v1",)
    assert profile.attributes["nested"]["countries"] == frozenset({"KE", "NVG"})


def test_profile_and_nested_attributes_are_not_mutable():
    profile = make_profile(attributes={"nested": {"values": [1, 2]}})
    with pytest.raises(FrozenInstanceError):
        profile.registry_id = "other.registry"
    with pytest.raises(TypeError):
        profile.attributes["new"] = "value"
    with pytest.raises(TypeError):
        profile.attributes["nested"]["new"] = "value"
    with pytest.raises(AttributeError):
        profile.attributes["nested"]["values"].append(3)


def test_to_dict_returns_deeply_detached_attributes():
    profile = make_profile(attributes={"nested": {"values": [1, 2]}})
    first = profile.to_dict()
    first["attributes"]["nested"]["values"].append(3)
    second = profile.to_dict()
    assert second["attributes"]["nested"]["values"] == [1, 2]


def test_attribute_keys_are_trimmed_and_remain_unique():
    profile = make_profile(attributes={" policy_reference ": "policy.v1"})
    assert list(profile.attributes) == ["policy_reference"]
    with pytest.raises(RegistryMetadataProfileError, match="remain unique"):
        make_profile(attributes={"policy": 1, " policy ": 2})


@pytest.mark.parametrize("attributes", [{"": 1}, {"   ": 1}])
def test_empty_attribute_keys_are_rejected(attributes):
    with pytest.raises(RegistryMetadataProfileError, match="cannot be empty"):
        make_profile(attributes=attributes)


def test_non_text_attribute_keys_are_rejected():
    with pytest.raises(TypeError, match="attribute keys must be text"):
        make_profile(attributes={1: "value"})
