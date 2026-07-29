from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import pytest
from registries.canonical.canonical_dataset_definition import CanonicalDatasetDefinition, CanonicalDatasetDefinitionError
from registries.canonical.canonical_dataset_reference import CanonicalDatasetReference
from registries.canonical.canonical_dataset_type import CanonicalDatasetType

NOW = datetime(2026, 7, 29, 16, 0, tzinfo=timezone.utc)
TYPE = CanonicalDatasetType("type.authoritative", "DATASET.AUTHORITATIVE", "Authoritative")

def make(**overrides):
    values = dict(dataset_id="dataset.novegeo.citizens", dataset_code="novegeo.citizens", dataset_name="NoveGeo Citizen Dataset", dataset_type=TYPE, authority_registry_id="registry.citizens", record_type_code="identity.person", schema_id="schema.citizen", schema_version=1, dataset_version=1, runtime_mode="simulation", created_at=NOW)
    values.update(overrides); return CanonicalDatasetDefinition(**values)

def test_valid_definition_normalises_fields():
    value = make(dataset_code=" novegeo.citizens ", record_type_code=" identity.person ", dataset_name=" Citizens ", runtime_mode=" SIMULATION ")
    assert (value.dataset_code, value.record_type_code, value.dataset_name, value.runtime_mode) == ("NOVEGEO.CITIZENS", "IDENTITY.PERSON", "Citizens", "simulation")

def test_reference_preserves_identity_version_and_runtime():
    assert make(dataset_version=3).reference == CanonicalDatasetReference("dataset.novegeo.citizens", 3, "simulation")

def test_display_name_does_not_define_identity():
    assert make(dataset_name="Citizens").dataset_id == make(dataset_name="National Persons").dataset_id

def test_person_names_and_team_labels_can_be_reserved_as_attributes_without_becoming_identity():
    value = make(attributes={"supported_contexts": ["document_name_assertion", "tournament_display_name"]})
    assert value.dataset_id == "dataset.novegeo.citizens"
    assert value.to_dict()["attributes"]["supported_contexts"][0] == "document_name_assertion"

def test_source_lineage_is_immutable_and_serialised():
    source = CanonicalDatasetReference("dataset.population.seed", 1, "simulation")
    value = make(source_datasets=[source])
    assert value.source_datasets == (source,)
    assert value.to_dict()["source_datasets"][0]["dataset_id"] == "dataset.population.seed"

def test_duplicate_and_self_sources_rejected():
    source = CanonicalDatasetReference("dataset.population.seed", 1, "simulation")
    with pytest.raises(CanonicalDatasetDefinitionError, match="unique"):
        make(source_datasets=[source, source])
    with pytest.raises(CanonicalDatasetDefinitionError, match="cannot cite itself"):
        make(source_datasets=[CanonicalDatasetReference("dataset.novegeo.citizens", 1, "simulation")])

def test_runtime_mode_keeps_simulation_and_production_distinct():
    assert make(runtime_mode="simulation") != make(runtime_mode="production")

def test_versions_reject_boolean_and_non_positive():
    for field in ("schema_version", "dataset_version"):
        with pytest.raises(TypeError): make(**{field: True})
        with pytest.raises(CanonicalDatasetDefinitionError): make(**{field: 0})

def test_created_at_must_be_aware_and_normalises_to_utc():
    with pytest.raises(CanonicalDatasetDefinitionError): make(created_at=datetime(2026, 1, 1))
    assert make(created_at=datetime(2026, 7, 29, 18, 0, tzinfo=timezone(timedelta(hours=2)))).created_at == NOW

def test_attributes_are_deeply_frozen():
    source = {"labels": ["Goalliers"]}; value = make(attributes=source); source["labels"].append("Changed")
    assert value.to_dict()["attributes"] == {"labels": ["Goalliers"]}
    with pytest.raises(TypeError): value.attributes["x"] = 1

def test_round_trip_and_z_datetime():
    value = make(source_datasets=[CanonicalDatasetReference("dataset.seed", 1, "simulation")], attributes={"scope": "national"})
    payload = value.to_dict(); payload["created_at"] = "2026-07-29T16:00:00Z"
    assert CanonicalDatasetDefinition.from_dict(payload) == value

def test_unknown_and_missing_fields_rejected():
    payload = make().to_dict(); payload["extra"] = 1
    with pytest.raises(CanonicalDatasetDefinitionError): CanonicalDatasetDefinition.from_dict(payload)
    payload = make().to_dict(); del payload["dataset_id"]
    with pytest.raises(CanonicalDatasetDefinitionError): CanonicalDatasetDefinition.from_dict(payload)

def test_frozen():
    with pytest.raises(FrozenInstanceError): make().dataset_name = "Changed"
