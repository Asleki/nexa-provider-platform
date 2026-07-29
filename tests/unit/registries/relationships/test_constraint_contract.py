from dataclasses import FrozenInstanceError

import pytest

from registries.relationships.constraint_contract import (
    RelationshipCardinality,
    RelationshipConstraint,
    RelationshipConstraintError,
    RelationshipDuplicatePolicy,
    RelationshipSelfReferencePolicy,
)
from registries.relationships.relationship_type import RelationshipType


def _type():
    return RelationshipType(
        "school.enrolled_at", "SCHOOL.ENROLLED_AT", "Enrolled at"
    )


def _constraint(**changes):
    values = {
        "constraint_id": "constraint.school-enrolment",
        "constraint_code": "CONSTRAINT.SCHOOL_ENROLMENT",
        "relationship_type": _type(),
        "allowed_source_registry_ids": ("citizens", "students"),
        "allowed_target_registry_ids": ("schools",),
        "source_cardinality": RelationshipCardinality(0, 1),
        "target_cardinality": RelationshipCardinality(0, None),
        "self_reference_policy": RelationshipSelfReferencePolicy.PROHIBIT,
        "duplicate_policy": RelationshipDuplicatePolicy.PROHIBIT,
        "runtime_modes": ("simulation", "production"),
        "description": "One current school relationship.",
        "version": 1,
    }
    values.update(changes)
    return RelationshipConstraint(**values)


def test_cardinality_accepts_bounded_and_unbounded_ranges():
    assert RelationshipCardinality(1, 3).allows_count(2)
    assert RelationshipCardinality(0, None).allows_count(1000)


def test_cardinality_rejects_counts_outside_bounds():
    cardinality = RelationshipCardinality(1, 2)
    assert cardinality.allows_count(0) is False
    assert cardinality.allows_count(3) is False


@pytest.mark.parametrize("minimum,maximum", [(-1, 1), (0, -1), (3, 2)])
def test_invalid_cardinality_ranges_are_rejected(minimum, maximum):
    with pytest.raises(RelationshipConstraintError):
        RelationshipCardinality(minimum, maximum)


@pytest.mark.parametrize("field", ["minimum", "maximum"])
def test_cardinality_rejects_boolean_values(field):
    values = {"minimum": 0, "maximum": 1}
    values[field] = True
    with pytest.raises(TypeError):
        RelationshipCardinality(**values)


def test_allows_count_rejects_invalid_count_type():
    with pytest.raises(TypeError):
        RelationshipCardinality().allows_count(True)


def test_cardinality_round_trip_is_deterministic():
    cardinality = RelationshipCardinality(1, None)
    assert RelationshipCardinality.from_dict(cardinality.to_dict()) == cardinality


def test_cardinality_from_dict_rejects_unknown_fields():
    with pytest.raises(RelationshipConstraintError):
        RelationshipCardinality.from_dict({"minimum": 0, "maximum": 1, "x": 2})


def test_constraint_normalises_identity_code_description_and_ordering():
    constraint = _constraint(
        constraint_id="  constraint.school-enrolment  ",
        constraint_code=" constraint.school_enrolment ",
        allowed_source_registry_ids=("students", "citizens"),
        runtime_modes=("simulation", "production"),
        description="  school rule  ",
    )
    assert constraint.constraint_id == "constraint.school-enrolment"
    assert constraint.constraint_code == "CONSTRAINT.SCHOOL_ENROLMENT"
    assert constraint.allowed_source_registry_ids == ("citizens", "students")
    assert constraint.runtime_modes == ("production", "simulation")
    assert constraint.description == "school rule"


def test_empty_endpoint_sets_mean_unrestricted():
    constraint = _constraint(
        allowed_source_registry_ids=(), allowed_target_registry_ids=()
    )
    assert constraint.allows_source_registry("any.registry")
    assert constraint.allows_target_registry("another.registry")


def test_endpoint_allow_lists_are_enforced():
    constraint = _constraint()
    assert constraint.allows_source_registry("citizens")
    assert constraint.allows_source_registry("banks") is False
    assert constraint.allows_target_registry("schools")
    assert constraint.allows_target_registry("hospitals") is False


def test_runtime_applicability_is_explicit():
    constraint = _constraint(runtime_modes=("simulation",))
    assert constraint.applies_to_runtime("SIMULATION")
    assert constraint.applies_to_runtime("production") is False


@pytest.mark.parametrize("field", ["constraint_id", "constraint_code"])
def test_required_constraint_identity_rejects_empty_text(field):
    with pytest.raises(RelationshipConstraintError):
        _constraint(**{field: "  "})


@pytest.mark.parametrize(
    "changes",
    [
        {"constraint_id": "bad value"},
        {"constraint_code": "SINGLE"},
        {"constraint_code": "CONSTRAINT.bad-code"},
        {"version": 0},
        {"version": -1},
    ],
)
def test_invalid_constraint_structure_is_rejected(changes):
    with pytest.raises(RelationshipConstraintError):
        _constraint(**changes)


def test_boolean_version_is_rejected():
    with pytest.raises(TypeError):
        _constraint(version=True)


def test_duplicate_allowed_registry_ids_are_rejected_after_normalisation():
    with pytest.raises(RelationshipConstraintError):
        _constraint(allowed_source_registry_ids=("citizens", " citizens "))


def test_duplicate_runtime_modes_are_rejected_after_normalisation():
    with pytest.raises(RelationshipConstraintError):
        _constraint(runtime_modes=("simulation", " SIMULATION "))


def test_empty_runtime_modes_are_rejected():
    with pytest.raises(RelationshipConstraintError):
        _constraint(runtime_modes=())


@pytest.mark.parametrize(
    "field,value",
    [
        ("relationship_type", object()),
        ("allowed_source_registry_ids", "citizens"),
        ("allowed_target_registry_ids", 1),
        ("source_cardinality", object()),
        ("target_cardinality", object()),
        ("self_reference_policy", "prohibit"),
        ("duplicate_policy", "prohibit"),
        ("runtime_modes", "simulation"),
        ("description", 1),
    ],
)
def test_wrong_constraint_field_types_are_rejected(field, value):
    with pytest.raises(TypeError):
        _constraint(**{field: value})


def test_constraint_is_frozen():
    constraint = _constraint()
    with pytest.raises(FrozenInstanceError):
        constraint.version = 2


def test_constraint_serialization_round_trip_is_deterministic():
    constraint = _constraint()
    payload = constraint.to_dict()
    rebuilt = RelationshipConstraint.from_dict(payload)
    assert rebuilt == constraint
    assert rebuilt.to_dict() == payload


def test_serialization_returns_detached_lists_and_nested_dicts():
    constraint = _constraint()
    payload = constraint.to_dict()
    payload["allowed_source_registry_ids"].append("banks")
    payload["relationship_type"]["relationship_type_name"] = "Changed"
    assert constraint.allowed_source_registry_ids == ("citizens", "students")
    assert constraint.relationship_type.relationship_type_name == "Enrolled at"


def test_from_dict_accepts_omitted_optional_fields():
    rebuilt = RelationshipConstraint.from_dict(
        {
            "constraint_id": "constraint.open",
            "constraint_code": "CONSTRAINT.OPEN",
            "relationship_type": _type().to_dict(),
        }
    )
    assert rebuilt.allowed_source_registry_ids == ()
    assert rebuilt.runtime_modes == ("production", "simulation")


def test_from_dict_rejects_unknown_fields():
    payload = _constraint().to_dict()
    payload["unexpected"] = True
    with pytest.raises(RelationshipConstraintError):
        RelationshipConstraint.from_dict(payload)


def test_from_dict_rejects_missing_required_fields():
    with pytest.raises(RelationshipConstraintError):
        RelationshipConstraint.from_dict({"constraint_id": "constraint.x"})


def test_from_dict_rejects_unknown_policy_values():
    payload = _constraint().to_dict()
    payload["duplicate_policy"] = "merge"
    with pytest.raises(RelationshipConstraintError):
        RelationshipConstraint.from_dict(payload)


def test_description_length_is_bounded():
    with pytest.raises(RelationshipConstraintError):
        _constraint(description="x" * 1001)
