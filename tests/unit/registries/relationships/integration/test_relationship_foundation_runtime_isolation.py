from datetime import datetime, timezone

from registries.relationships.constraint_contract import RelationshipConstraint
from registries.relationships.direction_contract import RelationshipDirection, RelationshipDirectionMode
from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_api_contract import RelationshipValidationRequest
from registries.relationships.relationship_constraint_rules import RelationshipConstraintContext
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType
from registries.relationships.relationship_validation_api import RelationshipValidationApi

NOW = datetime(2026, 7, 29, 18, 30, tzinfo=timezone.utc)
TYPE = RelationshipType("type-1", "GENERIC.RELATED_TO", "Related")

def request(*, relationship_runtime="simulation", constraint_modes=("simulation",), provenance_runtime="simulation", source_type="system", existing=None):
    rel = RelationshipDefinition("rel-1", TYPE, RegistryReference("registry-a", "a-1"), RegistryReference("registry-b", "b-1"), relationship_runtime, 1)
    direction = RelationshipDirection("dir-1", "DIRECTION.RELATED_TO", RelationshipDirectionMode.FORWARD_ONLY, TYPE)
    constraint = RelationshipConstraint("constraint-1", "CONSTRAINT.RELATED_TO", TYPE, ("registry-a",), ("registry-b",), runtime_modes=constraint_modes)
    provenance = RelationshipProvenance("prov-1", "rel-1", 1, provenance_runtime, source_type, "source-system", recorded_at=NOW)
    return RelationshipValidationRequest("req-1", rel, direction, constraint, RelationshipConstraintContext(), provenance, NOW, existing_relationship=existing)

def validate(value):
    return RelationshipValidationApi(clock=lambda: NOW).validate(value)

def test_production_relationship_rejects_simulation_provenance():
    result = validate(request(relationship_runtime="production", constraint_modes=("production",), provenance_runtime="simulation"))
    assert [item.code for item in result.findings] == ["RUNTIME_MODE_MISMATCH"]

def test_simulation_relationship_rejects_production_only_constraint():
    result = validate(request(constraint_modes=("production",)))
    assert [item.code for item in result.findings] == ["RUNTIME_MODE_NOT_ALLOWED"]

def test_production_baseline_rejects_simulation_proposal():
    baseline = RelationshipDefinition("rel-1", TYPE, RegistryReference("registry-a", "a-1"), RegistryReference("registry-b", "b-1"), "production", 1)
    result = validate(request(existing=baseline))
    assert result.findings[0].code == "RUNTIME_MODE_CHANGED"

def test_human_source_is_valid_in_simulation_runtime():
    assert validate(request(source_type="human")).is_valid

def test_system_source_is_valid_in_production_runtime():
    assert validate(request(relationship_runtime="production", constraint_modes=("production",), provenance_runtime="production", source_type="system")).is_valid
