from dataclasses import FrozenInstanceError

import pytest

from registries.canonical.canonical_dataset_type import CanonicalDatasetType, CanonicalDatasetTypeError


def make(**overrides):
    values = dict(
        dataset_type_id="dataset.type.authoritative",
        dataset_type_code="dataset.authoritative",
        dataset_type_name="Authoritative Dataset",
    )
    values.update(overrides)
    return CanonicalDatasetType(**values)


def test_normalises_semantic_fields():
    value = make(dataset_type_id=" dataset.type.authoritative ", dataset_type_code=" dataset.authoritative ", dataset_type_name=" Authoritative Dataset ", description=" Source of declared authority. ")
    assert value.dataset_type_id == "dataset.type.authoritative"
    assert value.dataset_type_code == "DATASET.AUTHORITATIVE"
    assert value.dataset_type_name == "Authoritative Dataset"
    assert value.description == "Source of declared authority."


def test_type_is_extensible_without_closed_enum():
    codes = {make().dataset_type_code, make(dataset_type_id="dataset.type.simulation_seed", dataset_type_code="SIMULATION.SEED", dataset_type_name="Simulation Seed").dataset_type_code}
    assert codes == {"DATASET.AUTHORITATIVE", "SIMULATION.SEED"}


def test_identity_is_independent_of_display_name():
    assert make(dataset_type_name="Authoritative").dataset_type_id == make(dataset_type_name="Primary Authority Dataset").dataset_type_id

@pytest.mark.parametrize("field", ["dataset_type_id", "dataset_type_code", "dataset_type_name"])
def test_required_fields_reject_empty(field):
    with pytest.raises(CanonicalDatasetTypeError):
        make(**{field: " "})


def test_code_requires_hierarchy():
    with pytest.raises(CanonicalDatasetTypeError, match="hierarchical dotted code"):
        make(dataset_type_code="AUTHORITATIVE")


def test_version_rejects_bool_and_non_positive():
    with pytest.raises(TypeError):
        make(version=True)
    with pytest.raises(CanonicalDatasetTypeError):
        make(version=0)


def test_attributes_are_deeply_frozen_and_detached():
    source = {"policy": {"labels": ["primary"]}}
    value = make(attributes=source)
    source["policy"]["labels"].append("changed")
    assert value.to_dict()["attributes"] == {"policy": {"labels": ["primary"]}}
    with pytest.raises(TypeError):
        value.attributes["x"] = 1


def test_duplicate_normalised_attribute_keys_rejected():
    with pytest.raises(CanonicalDatasetTypeError):
        make(attributes={"x": 1, " x ": 2})


def test_round_trip_and_unknown_field_rejection():
    value = make(attributes={"future": ["snapshot"]})
    assert CanonicalDatasetType.from_dict(value.to_dict()) == value
    payload = value.to_dict(); payload["extra"] = True
    with pytest.raises(CanonicalDatasetTypeError):
        CanonicalDatasetType.from_dict(payload)


def test_frozen():
    with pytest.raises(FrozenInstanceError):
        make().dataset_type_name = "Changed"
