from datetime import datetime, timezone

from registries.relationships.constraint_contract import RelationshipConstraint
from registries.relationships.direction_contract import RelationshipDirection, RelationshipDirectionMode
from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_api_contract import RelationshipValidationRequest, RelationshipValidationResult
from registries.relationships.relationship_constraint_rules import RelationshipConstraintContext
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType
from registries.relationships.relationship_validation_api import RelationshipValidationApi

NOW = datetime(2026, 7, 29, 19, 0, tzinfo=timezone.utc)

def request():
    rtype = RelationshipType("type-1", "GENERIC.RELATED_TO", "Related")
    rel = RelationshipDefinition("rel-1", rtype, RegistryReference("registry-a", "a-1"), RegistryReference("registry-b", "b-1"), "simulation", 1, attributes={"nested": {"values": [1, 2]}})
    direction = RelationshipDirection("dir-1", "DIRECTION.RELATED_TO", RelationshipDirectionMode.FORWARD_ONLY, rtype)
    constraint = RelationshipConstraint("constraint-1", "CONSTRAINT.RELATED_TO", rtype, ("registry-a",), ("registry-b",), runtime_modes=("production",))
    provenance = RelationshipProvenance("prov-1", "wrong-rel", 2, "production", "system", "nexilabs", recorded_at=NOW, attributes={"scenario": {"ids": ["s-1"]}})
    return RelationshipValidationRequest("req-1", rel, direction, constraint, RelationshipConstraintContext(), provenance, NOW, metadata={"batch": {"ids": ["b-1"]}})

def test_repeated_validation_is_identical_with_fixed_clock():
    api = RelationshipValidationApi(clock=lambda: NOW)
    first = api.validate(request())
    second = api.validate(request())
    assert first == second
    assert first.to_dict() == second.to_dict()

def test_finding_order_and_messages_are_stable():
    api = RelationshipValidationApi(clock=lambda: NOW)
    snapshots = [api.validate(request()).to_dict()["findings"] for _ in range(5)]
    assert snapshots.count(snapshots[0]) == 5

def test_complete_request_round_trip_is_equal():
    original = request()
    rebuilt = RelationshipValidationRequest.from_dict(original.to_dict())
    assert rebuilt == original

def test_result_round_trip_is_equal():
    result = RelationshipValidationApi(clock=lambda: NOW).validate(request())
    rebuilt = RelationshipValidationResult.from_dict(result.to_dict())
    assert rebuilt == result

def test_serialised_nested_values_are_detached():
    original = request()
    payload = original.to_dict()
    payload["relationship"]["attributes"]["nested"]["values"].append(3)
    payload["provenance"]["attributes"]["scenario"]["ids"].append("s-2")
    payload["metadata"]["batch"]["ids"].append("b-2")
    assert original.relationship.attributes["nested"]["values"] == (1, 2)
    assert original.provenance.attributes["scenario"]["ids"] == ("s-1",)
    assert original.metadata["batch"]["ids"] == ("b-1",)
