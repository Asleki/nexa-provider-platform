from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata.registry_provenance_source_type import RegistryProvenanceSourceType
from registries.relationships.provenance_contract import (
    RelationshipProvenance,
    RelationshipProvenanceError,
)

NOW = datetime(2026, 7, 29, 13, 0, tzinfo=timezone.utc)


def make(**overrides):
    values = dict(
        provenance_id="prov-001",
        relationship_id="rel-001",
        relationship_version=1,
        runtime_mode="simulation",
        source_type=RegistryProvenanceSourceType.SYSTEM,
        source_system="nexilabs",
        recorded_at=NOW,
    )
    values.update(overrides)
    return RelationshipProvenance(**values)


def test_valid_system_provenance():
    value = make(source_event_id="evt-001", correlation_id="corr-1", causation_id="cause-1")
    assert value.source_type is RegistryProvenanceSourceType.SYSTEM
    assert value.runtime_mode == "simulation"

@pytest.mark.parametrize("source_type", ["human", "institution", "system"])
def test_known_source_types(source_type):
    assert make(source_type=source_type).source_type.value == source_type


def test_valid_import():
    assert make(source_type="import", source_system="legacy", source_reference="old-1").source_type.value == "import"


def test_valid_derived():
    assert make(source_type="derived", source_system="analytics", reason="derived from payroll").reason


def test_valid_unknown():
    value = make(source_type="unknown", source_system="", reason="legacy source unavailable")
    assert value.source_type is RegistryProvenanceSourceType.UNKNOWN


def test_valid_simulation_generator():
    value = make(source_type="simulation_generator", generated=True, generator_name="population_generator", generator_version="1")
    assert value.generated


def test_text_normalisation():
    value = make(provenance_id=" prov-001 ", relationship_id=" rel-001 ", runtime_mode=" SIMULATION ", source_system=" nexilabs ")
    assert (value.provenance_id, value.relationship_id, value.runtime_mode, value.source_system) == ("prov-001", "rel-001", "simulation", "nexilabs")

@pytest.mark.parametrize("name", ["provenance_id", "relationship_id"])
def test_required_identifier_empty(name):
    with pytest.raises(RelationshipProvenanceError):
        make(**{name: " "})

@pytest.mark.parametrize("name", ["relationship_version", "version"])
def test_versions_reject_boolean(name):
    with pytest.raises(TypeError):
        make(**{name: True})

@pytest.mark.parametrize("name", ["relationship_version", "version"])
def test_versions_require_positive(name):
    with pytest.raises(RelationshipProvenanceError):
        make(**{name: 0})


def test_invalid_runtime_mode():
    with pytest.raises(RelationshipProvenanceError):
        make(runtime_mode="bad mode")


def test_known_source_requires_system():
    with pytest.raises(RelationshipProvenanceError):
        make(source_system="")


def test_unknown_rejects_system():
    with pytest.raises(RelationshipProvenanceError):
        make(source_type="unknown", source_system="x", reason="missing")


def test_unknown_requires_reason():
    with pytest.raises(RelationshipProvenanceError):
        make(source_type="unknown", source_system="")


def test_unknown_cannot_be_verified():
    with pytest.raises(RelationshipProvenanceError):
        make(source_type="unknown", source_system="", reason="missing", verified=True, verification_reference="v")


def test_generator_source_requires_generated():
    with pytest.raises(RelationshipProvenanceError):
        make(source_type="simulation_generator")


def test_generated_requires_generator_source():
    with pytest.raises(RelationshipProvenanceError):
        make(generated=True, generator_name="x")


def test_generated_requires_reference():
    with pytest.raises(RelationshipProvenanceError):
        make(source_type="simulation_generator", generated=True)


def test_generator_version_requires_name():
    with pytest.raises(RelationshipProvenanceError):
        make(source_type="simulation_generator", generated=True, generation_batch_id="b", generator_version="1")


def test_non_generated_rejects_generator_details():
    with pytest.raises(RelationshipProvenanceError):
        make(generator_name="x")

@pytest.mark.parametrize("source_type", ["import", "derived"])
def test_import_and_derived_require_reference_event_or_reason(source_type):
    with pytest.raises(RelationshipProvenanceError):
        make(source_type=source_type)


def test_recorded_at_must_be_aware():
    with pytest.raises(RelationshipProvenanceError):
        make(recorded_at=datetime(2026, 1, 1))


def test_recorded_at_normalises_to_utc():
    value = make(recorded_at=datetime(2026, 7, 29, 15, 0, tzinfo=timezone(timedelta(hours=2))))
    assert value.recorded_at == NOW


def test_verified_requires_time_or_reference():
    with pytest.raises(RelationshipProvenanceError):
        make(verified=True)


def test_unverified_rejects_verification_details():
    with pytest.raises(RelationshipProvenanceError):
        make(verification_reference="proof")


def test_verified_at_not_before_recorded_at():
    with pytest.raises(RelationshipProvenanceError):
        make(verified=True, verified_at=NOW - timedelta(seconds=1))


def test_valid_verification():
    value = make(verified=True, verified_at=NOW + timedelta(seconds=1), verification_reference="proof")
    assert value.verified


def test_attributes_deeply_frozen():
    source = {"scenario": {"steps": [1, 2]}}
    value = make(attributes=source)
    source["scenario"]["steps"].append(3)
    assert value.to_dict()["attributes"] == {"scenario": {"steps": [1, 2]}}
    with pytest.raises(TypeError):
        value.attributes["x"] = 1


def test_duplicate_normalised_attribute_keys_rejected():
    with pytest.raises(RelationshipProvenanceError):
        make(attributes={"a": 1, " a ": 2})


def test_frozen_dataclass():
    value = make()
    with pytest.raises(FrozenInstanceError):
        value.runtime_mode = "production"


def test_to_dict_is_detached():
    value = make(attributes={"a": [1]})
    data = value.to_dict()
    data["attributes"]["a"].append(2)
    assert value.to_dict()["attributes"] == {"a": [1]}


def test_round_trip():
    value = make(source_actor_id="actor-1", attributes={"scenario_id": "s-1"})
    assert RelationshipProvenance.from_dict(value.to_dict()) == value


def test_from_dict_accepts_z_datetime():
    data = make().to_dict()
    data["recorded_at"] = "2026-07-29T13:00:00Z"
    assert RelationshipProvenance.from_dict(data).recorded_at == NOW


def test_from_dict_rejects_unknown_fields():
    data = make().to_dict()
    data["extra"] = 1
    with pytest.raises(RelationshipProvenanceError):
        RelationshipProvenance.from_dict(data)


def test_from_dict_rejects_missing_required_fields():
    data = make().to_dict()
    del data["relationship_id"]
    with pytest.raises(RelationshipProvenanceError):
        RelationshipProvenance.from_dict(data)

@pytest.mark.parametrize("field", ["generated", "verified"])
def test_boolean_fields_require_boolean(field):
    with pytest.raises(TypeError):
        make(**{field: 1})
