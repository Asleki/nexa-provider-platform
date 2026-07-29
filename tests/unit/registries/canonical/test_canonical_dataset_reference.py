from dataclasses import FrozenInstanceError

import pytest

from registries.canonical.canonical_dataset_reference import CanonicalDatasetReference, CanonicalDatasetReferenceError


def make(**overrides):
    values = dict(dataset_id="dataset.novegeo.citizens", dataset_version=1, runtime_mode="simulation")
    values.update(overrides)
    return CanonicalDatasetReference(**values)


def test_normalises_identity_and_runtime():
    value = make(dataset_id=" dataset.novegeo.citizens ", runtime_mode=" SIMULATION ")
    assert value.dataset_id == "dataset.novegeo.citizens"
    assert value.runtime_mode == "simulation"


def test_same_dataset_can_have_multiple_versions_without_identity_change():
    assert make(dataset_version=1).dataset_id == make(dataset_version=2).dataset_id
    assert make(dataset_version=1) != make(dataset_version=2)


def test_simulation_and_production_references_remain_distinct():
    assert make(runtime_mode="simulation") != make(runtime_mode="production")

@pytest.mark.parametrize("field", ["dataset_id", "runtime_mode"])
def test_required_text_rejects_empty(field):
    with pytest.raises(CanonicalDatasetReferenceError):
        make(**{field: " "})


def test_invalid_identifier_and_runtime_are_rejected():
    with pytest.raises(CanonicalDatasetReferenceError):
        make(dataset_id="bad id")
    with pytest.raises(CanonicalDatasetReferenceError):
        make(runtime_mode="bad mode")


def test_version_rejects_bool_and_non_positive():
    with pytest.raises(TypeError):
        make(dataset_version=True)
    with pytest.raises(CanonicalDatasetReferenceError):
        make(dataset_version=0)


def test_attributes_are_deeply_frozen():
    source = {"partition": {"regions": ["north"]}}
    value = make(attributes=source)
    source["partition"]["regions"].append("south")
    assert value.to_dict()["attributes"] == {"partition": {"regions": ["north"]}}
    with pytest.raises(TypeError):
        value.attributes["x"] = 1


def test_round_trip_and_unknown_field_rejection():
    value = make(attributes={"scope": "national"})
    assert CanonicalDatasetReference.from_dict(value.to_dict()) == value
    payload = value.to_dict(); payload["extra"] = 1
    with pytest.raises(CanonicalDatasetReferenceError):
        CanonicalDatasetReference.from_dict(payload)


def test_frozen():
    with pytest.raises(FrozenInstanceError):
        make().runtime_mode = "production"
