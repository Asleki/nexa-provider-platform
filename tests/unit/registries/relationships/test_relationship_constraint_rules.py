from dataclasses import FrozenInstanceError

import pytest

from registries.relationships.constraint_contract import (
    RelationshipCardinality,
    RelationshipConstraint,
    RelationshipDuplicatePolicy,
    RelationshipSelfReferencePolicy,
)
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_constraint_rules import (
    RelationshipConstraintContext,
    RelationshipConstraintFinding,
    RelationshipConstraintResult,
    RelationshipConstraintRuleError,
    RelationshipConstraintViolation,
    RelationshipConstraintViolationCode,
    assert_relationship_constraints,
    evaluate_relationship_constraints,
)
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType


def _type():
    return RelationshipType(
        "school.enrolled_at", "SCHOOL.ENROLLED_AT", "Enrolled at"
    )


def _reference(registry_id="students", record_id="student-1", version=1):
    return RegistryReference(registry_id, record_id, version)


def _relationship(**changes):
    values = {
        "relationship_id": "relationship-1",
        "relationship_type": _type(),
        "source": _reference(),
        "target": _reference("schools", "school-1"),
        "runtime_mode": "simulation",
    }
    values.update(changes)
    return RelationshipDefinition(**values)


def _constraint(**changes):
    values = {
        "constraint_id": "constraint.school-enrolment",
        "constraint_code": "CONSTRAINT.SCHOOL_ENROLMENT",
        "relationship_type": _type(),
        "allowed_source_registry_ids": ("students",),
        "allowed_target_registry_ids": ("schools",),
        "source_cardinality": RelationshipCardinality(0, 1),
        "target_cardinality": RelationshipCardinality(0, None),
        "self_reference_policy": RelationshipSelfReferencePolicy.PROHIBIT,
        "duplicate_policy": RelationshipDuplicatePolicy.PROHIBIT,
        "runtime_modes": ("simulation",),
    }
    values.update(changes)
    return RelationshipConstraint(**values)


def test_compatible_relationship_returns_empty_result():
    assert evaluate_relationship_constraints(_relationship(), _constraint()) == (
        RelationshipConstraintResult.compatible()
    )


def test_default_context_uses_zero_existing_counts():
    assert evaluate_relationship_constraints(_relationship(), _constraint()).is_compatible


def test_relationship_type_mismatch_is_reported():
    other = RelationshipType("school.teaches", "SCHOOL.TEACHES", "Teaches")
    result = evaluate_relationship_constraints(
        _relationship(relationship_type=other), _constraint()
    )
    assert result.violations == (
        RelationshipConstraintViolationCode.RELATIONSHIP_TYPE_MISMATCH,
    )


def test_non_identity_type_metadata_does_not_cause_mismatch():
    equivalent = RelationshipType(
        "school.enrolled_at", "SCHOOL.ENROLLED_AT", "Different display name"
    )
    assert evaluate_relationship_constraints(
        _relationship(relationship_type=equivalent), _constraint()
    ).is_compatible


def test_runtime_mode_not_allowed_is_reported():
    result = evaluate_relationship_constraints(
        _relationship(runtime_mode="production"), _constraint()
    )
    assert result.violations == (
        RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED,
    )


def test_source_registry_not_allowed_is_reported():
    result = evaluate_relationship_constraints(
        _relationship(source=_reference("citizens", "citizen-1")), _constraint()
    )
    assert result.violations == (
        RelationshipConstraintViolationCode.SOURCE_REGISTRY_NOT_ALLOWED,
    )


def test_target_registry_not_allowed_is_reported():
    result = evaluate_relationship_constraints(
        _relationship(target=_reference("banks", "bank-1")), _constraint()
    )
    assert result.violations == (
        RelationshipConstraintViolationCode.TARGET_REGISTRY_NOT_ALLOWED,
    )


def test_empty_endpoint_sets_are_unrestricted():
    constraint = _constraint(
        allowed_source_registry_ids=(), allowed_target_registry_ids=()
    )
    relationship = _relationship(
        source=_reference("citizens", "citizen-1"),
        target=_reference("hospitals", "hospital-1"),
    )
    assert evaluate_relationship_constraints(relationship, constraint).is_compatible


def test_self_reference_is_rejected_when_prohibited():
    reference = _reference("citizens", "citizen-1")
    relationship = _relationship(source=reference, target=reference)
    constraint = _constraint(
        allowed_source_registry_ids=("citizens",),
        allowed_target_registry_ids=("citizens",),
    )
    assert evaluate_relationship_constraints(relationship, constraint).violations == (
        RelationshipConstraintViolationCode.SELF_REFERENCE_PROHIBITED,
    )


def test_self_reference_is_allowed_when_declared():
    reference = _reference("categories", "category-1")
    relationship = _relationship(source=reference, target=reference)
    constraint = _constraint(
        allowed_source_registry_ids=("categories",),
        allowed_target_registry_ids=("categories",),
        self_reference_policy=RelationshipSelfReferencePolicy.ALLOW,
    )
    assert evaluate_relationship_constraints(relationship, constraint).is_compatible


def test_different_reference_versions_are_not_the_same_endpoint_identity():
    relationship = _relationship(
        source=_reference("citizens", "citizen-1", 1),
        target=_reference("citizens", "citizen-1", 2),
    )
    constraint = _constraint(
        allowed_source_registry_ids=("citizens",),
        allowed_target_registry_ids=("citizens",),
    )
    assert evaluate_relationship_constraints(relationship, constraint).is_compatible


def test_duplicate_pair_is_rejected_when_prohibited():
    context = RelationshipConstraintContext(existing_pair_count=1)
    assert evaluate_relationship_constraints(
        _relationship(), _constraint(), context
    ).violations == (
        RelationshipConstraintViolationCode.DUPLICATE_PAIR_PROHIBITED,
    )


def test_duplicate_pair_is_allowed_when_declared():
    constraint = _constraint(duplicate_policy=RelationshipDuplicatePolicy.ALLOW)
    context = RelationshipConstraintContext(existing_pair_count=10)
    assert evaluate_relationship_constraints(
        _relationship(), constraint, context
    ).is_compatible


def test_source_cardinality_uses_resulting_count():
    context = RelationshipConstraintContext(existing_source_count=1)
    assert evaluate_relationship_constraints(
        _relationship(), _constraint(), context
    ).violations == (
        RelationshipConstraintViolationCode.SOURCE_CARDINALITY_EXCEEDED,
    )


def test_target_cardinality_uses_resulting_count():
    constraint = _constraint(target_cardinality=RelationshipCardinality(0, 2))
    context = RelationshipConstraintContext(existing_target_count=2)
    assert evaluate_relationship_constraints(
        _relationship(), constraint, context
    ).violations == (
        RelationshipConstraintViolationCode.TARGET_CARDINALITY_EXCEEDED,
    )


def test_unbounded_cardinality_never_rejects_large_counts():
    constraint = _constraint(
        source_cardinality=RelationshipCardinality(0, None),
        target_cardinality=RelationshipCardinality(0, None),
    )
    context = RelationshipConstraintContext(1_000_000, 1_000_000, 0)
    assert evaluate_relationship_constraints(
        _relationship(), constraint, context
    ).is_compatible


def test_minimum_cardinality_is_not_enforced_during_creation_evaluation():
    constraint = _constraint(
        source_cardinality=RelationshipCardinality(5, None),
        target_cardinality=RelationshipCardinality(5, None),
    )
    assert evaluate_relationship_constraints(
        _relationship(), constraint
    ).is_compatible


def test_multiple_findings_are_returned_in_deterministic_order():
    other = RelationshipType("other.type", "OTHER.TYPE", "Other")
    same = _reference("banks", "record-1")
    relationship = _relationship(
        relationship_type=other,
        source=same,
        target=same,
        runtime_mode="production",
    )
    context = RelationshipConstraintContext(1, 1, 1)
    result = evaluate_relationship_constraints(relationship, _constraint(), context)
    assert result.violations == (
        RelationshipConstraintViolationCode.RELATIONSHIP_TYPE_MISMATCH,
        RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED,
        RelationshipConstraintViolationCode.SOURCE_REGISTRY_NOT_ALLOWED,
        RelationshipConstraintViolationCode.TARGET_REGISTRY_NOT_ALLOWED,
        RelationshipConstraintViolationCode.SELF_REFERENCE_PROHIBITED,
        RelationshipConstraintViolationCode.DUPLICATE_PAIR_PROHIBITED,
        RelationshipConstraintViolationCode.SOURCE_CARDINALITY_EXCEEDED,
    )


def test_assert_returns_none_for_compatible_relationship():
    assert assert_relationship_constraints(_relationship(), _constraint()) is None


def test_assert_raises_structured_violation():
    with pytest.raises(RelationshipConstraintViolation) as captured:
        assert_relationship_constraints(
            _relationship(),
            _constraint(),
            RelationshipConstraintContext(existing_source_count=1),
        )
    assert captured.value.result.violations == (
        RelationshipConstraintViolationCode.SOURCE_CARDINALITY_EXCEEDED,
    )


def test_compatible_result_cannot_raise_violation():
    with pytest.raises(ValueError):
        RelationshipConstraintViolation(RelationshipConstraintResult.compatible())


def test_finding_requires_valid_code_and_message():
    with pytest.raises(TypeError):
        RelationshipConstraintFinding("BAD", "message")
    with pytest.raises(ValueError):
        RelationshipConstraintFinding(
            RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED, "  "
        )


def test_result_rejects_duplicate_finding_codes():
    one = RelationshipConstraintFinding(
        RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED, "one"
    )
    two = RelationshipConstraintFinding(
        RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED, "two"
    )
    with pytest.raises(ValueError):
        RelationshipConstraintResult.from_findings(one, two)


def test_result_serialization_is_deterministic():
    finding = RelationshipConstraintFinding(
        RelationshipConstraintViolationCode.DUPLICATE_PAIR_PROHIBITED,
        "duplicate pair",
    )
    assert RelationshipConstraintResult.from_findings(finding).to_dict() == {
        "is_compatible": False,
        "violations": ["DUPLICATE_PAIR_PROHIBITED"],
        "findings": [
            {
                "code": "DUPLICATE_PAIR_PROHIBITED",
                "message": "duplicate pair",
            }
        ],
    }


def test_context_round_trip_is_deterministic():
    context = RelationshipConstraintContext(1, 2, 3)
    assert RelationshipConstraintContext.from_dict(context.to_dict()) == context


@pytest.mark.parametrize(
    "field", ["existing_source_count", "existing_target_count", "existing_pair_count"]
)
def test_context_rejects_negative_counts(field):
    values = {
        "existing_source_count": 0,
        "existing_target_count": 0,
        "existing_pair_count": 0,
    }
    values[field] = -1
    with pytest.raises(RelationshipConstraintRuleError):
        RelationshipConstraintContext(**values)


@pytest.mark.parametrize(
    "field", ["existing_source_count", "existing_target_count", "existing_pair_count"]
)
def test_context_rejects_boolean_counts(field):
    values = {
        "existing_source_count": 0,
        "existing_target_count": 0,
        "existing_pair_count": 0,
    }
    values[field] = True
    with pytest.raises(TypeError):
        RelationshipConstraintContext(**values)


def test_context_from_dict_rejects_unknown_fields():
    with pytest.raises(RelationshipConstraintRuleError):
        RelationshipConstraintContext.from_dict({"unexpected": 1})


@pytest.mark.parametrize(
    "relationship,constraint,context",
    [
        (object(), _constraint(), None),
        (_relationship(), object(), None),
        (_relationship(), _constraint(), object()),
    ],
)
def test_evaluator_rejects_wrong_input_types(relationship, constraint, context):
    with pytest.raises(TypeError):
        evaluate_relationship_constraints(relationship, constraint, context)


def test_context_and_contract_are_frozen():
    context = RelationshipConstraintContext()
    finding = RelationshipConstraintFinding(
        RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED, "blocked"
    )
    with pytest.raises(FrozenInstanceError):
        context.existing_pair_count = 1
    with pytest.raises(FrozenInstanceError):
        finding.message = "changed"


def test_evaluation_does_not_mutate_relationship_constraint_or_context():
    relationship = _relationship()
    constraint = _constraint()
    context = RelationshipConstraintContext()
    before = (relationship.to_dict(), constraint.to_dict(), context.to_dict())
    evaluate_relationship_constraints(relationship, constraint, context)
    assert (relationship.to_dict(), constraint.to_dict(), context.to_dict()) == before
