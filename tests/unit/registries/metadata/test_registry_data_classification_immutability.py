from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from registries.metadata import RegistryDataClassification


def test_classification_is_frozen():
    item = RegistryDataClassification("internal", "Operational metadata")
    with pytest.raises(FrozenInstanceError):
        item.reason = "Changed"


def test_categories_and_top_level_attributes_are_immutable():
    item = RegistryDataClassification(
        "restricted",
        "Citizen data",
        data_categories=["PERSONAL.IDENTITY"],
        attributes={"policy": "P-001"},
    )
    assert isinstance(item.data_categories, tuple)
    assert isinstance(item.attributes, MappingProxyType)
    with pytest.raises(TypeError):
        item.attributes["policy"] = "P-002"


def test_nested_mapping_list_and_set_values_are_frozen():
    item = RegistryDataClassification(
        "restricted",
        "Citizen data",
        attributes={
            "mapping": {"enabled": True},
            "list": ["one", "two"],
            "set": {"A", "B"},
        },
    )

    assert isinstance(item.attributes["mapping"], MappingProxyType)
    assert item.attributes["list"] == ("one", "two")
    assert item.attributes["set"] == frozenset({"A", "B"})

    with pytest.raises(TypeError):
        item.attributes["mapping"]["enabled"] = False
    with pytest.raises(AttributeError):
        item.attributes["list"].append("three")
    with pytest.raises(AttributeError):
        item.attributes["set"].add("C")


def test_caller_mutation_cannot_change_classification_snapshot():
    categories = ["PERSONAL.IDENTITY"]
    attributes = {
        "nested": {"codes": ["A"]},
        "members": {"one"},
    }
    item = RegistryDataClassification(
        "restricted",
        "Citizen data",
        data_categories=categories,
        attributes=attributes,
    )

    categories.append("PERSONAL.CONTACT")
    attributes["nested"]["codes"].append("B")
    attributes["members"].add("two")

    assert item.data_categories == ("PERSONAL.IDENTITY",)
    assert item.to_dict()["attributes"] == {
        "nested": {"codes": ["A"]},
        "members": ["one"],
    }
