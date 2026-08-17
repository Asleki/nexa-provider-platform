import pytest

from registries.nngla.spatial_fabric.bundle17c.contracts import CompatibilityOutcome, RelationshipType
from registries.nngla.spatial_fabric.bundle17c.compatibility import compatibility_rules


def test_bundle17c_relationship_enum_is_stable_and_explicit():
    assert [item.value for item in RelationshipType] == [
        "CONTAINS", "WITHIN", "INTERSECTS", "CROSSES", "TOUCHES", "OVERLAPS",
        "ADJACENT_TO", "NEAR", "FRONTS", "CONNECTED_TO",
    ]


def test_bundle17c_compatibility_outcome_keeps_policy_states_semantically_distinct():
    assert {item.value for item in CompatibilityOutcome} == {"ALLOW", "ALLOW_WITH_CONDITION", "REVIEW_REQUIRED", "BLOCK", "NOT_EVALUABLE"}
    assert any(rule.compatibility_outcome is CompatibilityOutcome.BLOCK for rule in compatibility_rules())
