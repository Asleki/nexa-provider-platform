from datetime import datetime, timezone

from registries.metadata.registry_provenance_source_type import RegistryProvenanceSourceType
from registries.relationships.constraint_contract import RelationshipCardinality, RelationshipConstraint, RelationshipDuplicatePolicy, RelationshipSelfReferencePolicy
from registries.relationships.direction_contract import RelationshipDirection, RelationshipDirectionMode
from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_api_contract import RelationshipValidationRequest
from registries.relationships.relationship_constraint_rules import RelationshipConstraintContext
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType
from registries.relationships.relationship_validation_api import RelationshipValidationApi

NOW = datetime(2026, 7, 29, 17, 30, tzinfo=timezone.utc)

def package(*, runtime="simulation", source_registry="students", target_registry="schools", code="EDUCATION.ENROLLED_AT", source_type="simulation_generator", existing=None, metadata=None):
    rtype = RelationshipType("type-1", code, "Relationship")
    rel = RelationshipDefinition("rel-1", rtype, RegistryReference(source_registry, "source-1"), RegistryReference(target_registry, "target-1"), runtime, 1)
    direction = RelationshipDirection("dir-1", "DIRECTION.TEST", RelationshipDirectionMode.FORWARD_ONLY, rtype)
    constraint = RelationshipConstraint(
        "constraint-1", "CONSTRAINT.TEST", rtype,
        (source_registry,), (target_registry,),
        RelationshipCardinality(0, 1), RelationshipCardinality(0, None),
        RelationshipSelfReferencePolicy.PROHIBIT, RelationshipDuplicatePolicy.PROHIBIT,
        (runtime,), version=1,
    )
    prov_kwargs = dict(provenance_id="prov-1", relationship_id="rel-1", relationship_version=1, runtime_mode=runtime, source_type=source_type, source_system="nexilabs", recorded_at=NOW)
    if source_type == RegistryProvenanceSourceType.SIMULATION_GENERATOR.value:
        prov_kwargs.update(generated=True, generator_name="population-generator", generation_batch_id="NVG-FOUNDATION-0001")
    provenance = RelationshipProvenance(**prov_kwargs)
    return RelationshipValidationRequest("req-1", rel, direction, constraint, RelationshipConstraintContext(), provenance, NOW, existing_relationship=existing, metadata=metadata or {})

def api():
    return RelationshipValidationApi(clock=lambda: NOW)

def test_complete_simulation_school_enrolment_is_valid():
    result = api().validate(package())
    assert result.is_valid
    assert result.metadata == {"validation_only": True, "persisted": False, "approved": False}

def test_complete_production_employment_package_is_valid():
    request = package(runtime="production", source_registry="citizens", target_registry="businesses", code="EMPLOYMENT.EMPLOYED_BY", source_type="human")
    assert api().validate(request).is_valid

def test_account_maintaining_bank_package_is_valid_and_round_trips():
    request = package(runtime="production", source_registry="accounts", target_registry="banks", code="BANKING.MAINTAINED_BY", source_type="system", metadata={"domain": {"name": "banking"}})
    rebuilt = RelationshipValidationRequest.from_dict(request.to_dict())
    assert rebuilt == request
    assert api().validate(rebuilt).is_valid

def test_household_generation_provenance_is_preserved():
    request = package(source_registry="citizens", target_registry="households", code="HOUSEHOLD.MEMBER_OF")
    assert request.provenance.generation_batch_id == "NVG-FOUNDATION-0001"
    assert api().validate(request).is_valid

def test_nexapos_compatible_device_assignment_stays_reference_only():
    request = package(runtime="production", source_registry="devices", target_registry="estates", code="DEVICE.REGISTERED_TO", source_type="system")
    payload = request.to_dict()
    assert set(payload["relationship"]["source"]) == {"registry_id", "record_id", "version", "attributes"}
    assert api().validate(request).is_valid

def test_compatible_existing_relationship_is_valid():
    request = package()
    existing = request.relationship
    request = package(existing=existing)
    assert api().validate(request).is_valid
