from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from registries.relationships.constraint_contract import RelationshipCardinality, RelationshipConstraint, RelationshipDuplicatePolicy, RelationshipSelfReferencePolicy
from registries.relationships.direction_contract import RelationshipDirection, RelationshipDirectionMode
from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_api_contract import RelationshipApiSubsystem, RelationshipValidationRequest
from registries.relationships.relationship_constraint_rules import RelationshipConstraintContext
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType
from registries.relationships.relationship_validation_api import RelationshipValidationApi

NOW = datetime(2026, 7, 29, 18, 0, tzinfo=timezone.utc)

def build(**overrides):
    good_type = RelationshipType("type-1", "EDUCATION.ENROLLED_AT", "Enrolment")
    rel = overrides.get("relationship", RelationshipDefinition("rel-1", good_type, RegistryReference("students", "student-1"), RegistryReference("schools", "school-1"), "simulation", 1))
    direction = overrides.get("direction", RelationshipDirection("dir-1", "DIRECTION.ENROLLED_AT", RelationshipDirectionMode.FORWARD_ONLY, good_type))
    constraint = overrides.get("constraint", RelationshipConstraint("constraint-1", "CONSTRAINT.ENROLLED_AT", good_type, ("students",), ("schools",), RelationshipCardinality(0, 1), RelationshipCardinality(0, 1), RelationshipSelfReferencePolicy.PROHIBIT, RelationshipDuplicatePolicy.PROHIBIT, ("simulation",)))
    provenance = overrides.get("provenance", RelationshipProvenance("prov-1", "rel-1", 1, "simulation", "system", "nexilabs", recorded_at=NOW))
    return RelationshipValidationRequest("req-1", rel, direction, constraint, overrides.get("context", RelationshipConstraintContext()), provenance, NOW, existing_relationship=overrides.get("existing"), metadata={"nested": {"items": ["a"]}})

def validate(request):
    return RelationshipValidationApi(clock=lambda: NOW).validate(request)

def test_all_subsystems_report_without_short_circuiting():
    wrong_type = RelationshipType("type-2", "EDUCATION.TEACHES", "Teaches")
    request = build(
        existing=RelationshipDefinition("old-rel", RelationshipType("type-1", "EDUCATION.ENROLLED_AT", "Enrolment"), RegistryReference("students", "student-1"), RegistryReference("schools", "school-1"), "simulation", 1),
        direction=RelationshipDirection("dir-2", "DIRECTION.TEACHES", RelationshipDirectionMode.FORWARD_ONLY, wrong_type),
        constraint=RelationshipConstraint("constraint-2", "CONSTRAINT.TEACHES", wrong_type, ("teachers",), ("schools",), runtime_modes=("simulation",)),
        provenance=RelationshipProvenance("prov-2", "other-rel", 2, "production", "system", "nexilabs", recorded_at=NOW),
    )
    result = validate(request)
    assert [item.subsystem for item in result.findings] == [
        RelationshipApiSubsystem.IMMUTABLE_REFERENCE,
        RelationshipApiSubsystem.DIRECTION,
        RelationshipApiSubsystem.CONSTRAINT,
        RelationshipApiSubsystem.CONSTRAINT,
        RelationshipApiSubsystem.PROVENANCE,
        RelationshipApiSubsystem.PROVENANCE,
        RelationshipApiSubsystem.PROVENANCE,
    ]

def test_self_reference_duplicate_and_both_cardinality_limits_are_reported():
    same = RegistryReference("students", "student-1")
    base = build()
    rel = RelationshipDefinition("rel-1", base.relationship.relationship_type, same, same, "simulation", 1)
    constraint = RelationshipConstraint("constraint-1", "CONSTRAINT.TEST", base.relationship.relationship_type, ("students",), ("students",), RelationshipCardinality(0, 1), RelationshipCardinality(0, 1), RelationshipSelfReferencePolicy.PROHIBIT, RelationshipDuplicatePolicy.PROHIBIT, ("simulation",))
    result = validate(build(relationship=rel, constraint=constraint, context=RelationshipConstraintContext(1, 1, 1)))
    assert [item.code for item in result.findings] == ["SELF_REFERENCE_PROHIBITED", "DUPLICATE_PAIR_PROHIBITED", "SOURCE_CARDINALITY_EXCEEDED", "TARGET_CARDINALITY_EXCEEDED"]

def test_failed_validation_does_not_mutate_request():
    request = build(provenance=RelationshipProvenance("prov-2", "other-rel", 1, "simulation", "system", "nexilabs", recorded_at=NOW))
    before = request.to_dict()
    validate(request)
    assert request.to_dict() == before

def test_request_and_nested_metadata_are_immutable():
    request = build()
    with pytest.raises(FrozenInstanceError):
        request.request_id = "changed"
    with pytest.raises(TypeError):
        request.metadata["nested"] = {}
    with pytest.raises(TypeError):
        request.metadata["nested"]["items"] += ("b",)

def test_serialised_mutation_is_detached_from_request():
    request = build()
    payload = request.to_dict()
    payload["metadata"]["nested"]["items"].append("changed")
    assert request.metadata["nested"]["items"] == ("a",)
