import pytest

from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.direction_contract import (
    RelationshipDirection,
    RelationshipDirectionMode,
)
from registries.relationships.relationship_direction_rules import (
    RelationshipDirectionFinding,
    RelationshipDirectionResult,
    RelationshipDirectionRuleError,
    RelationshipDirectionViolation,
    RelationshipDirectionViolationCode,
    RelationshipOrientation,
    assert_relationship_direction,
    evaluate_relationship_direction,
)
from registries.relationships.relationship_type import RelationshipType


def _forward_type():
    return RelationshipType("school.enrolled_at", "SCHOOL.ENROLLED_AT", "Enrolled at")


def _inverse_type():
    return RelationshipType("school.has_student", "SCHOOL.HAS_STUDENT", "Has student")


def _reference(registry_id, record_id):
    return RegistryReference(registry_id, record_id, 1)


def _relationship(
    relationship_type=None,
    source=None,
    target=None,
    runtime_mode="simulation",
    relationship_id="relationship-1",
):
    return RelationshipDefinition(
        relationship_id=relationship_id,
        relationship_type=relationship_type or _forward_type(),
        source=source or _reference("citizens", "citizen-1"),
        target=target or _reference("schools", "school-1"),
        runtime_mode=runtime_mode,
    )


def _direction(mode=RelationshipDirectionMode.INVERSE):
    return RelationshipDirection(
        direction_id="direction.school-enrolment",
        direction_code="DIRECTION.SCHOOL_ENROLMENT",
        mode=mode,
        forward_type=_forward_type(),
        inverse_type=_inverse_type() if mode is RelationshipDirectionMode.INVERSE else None,
    )


def test_forward_candidate_is_classified_as_forward():
    accepted = _relationship()
    result = evaluate_relationship_direction(accepted, _relationship(), _direction())
    assert result == RelationshipDirectionResult.forward()
    assert result.is_valid is True


def test_inverse_candidate_is_classified_as_reverse():
    accepted = _relationship()
    candidate = _relationship(
        relationship_type=_inverse_type(),
        source=accepted.target,
        target=accepted.source,
    )
    result = evaluate_relationship_direction(accepted, candidate, _direction())
    assert result == RelationshipDirectionResult.reverse()


def test_symmetric_candidate_uses_same_type_in_reverse():
    symmetric_type = RelationshipType("family.married", "FAMILY.MARRIED_TO", "Married")
    accepted = _relationship(relationship_type=symmetric_type)
    direction = RelationshipDirection(
        "direction.marriage", "DIRECTION.MARRIAGE", RelationshipDirectionMode.SYMMETRIC, symmetric_type
    )
    candidate = _relationship(
        relationship_type=symmetric_type,
        source=accepted.target,
        target=accepted.source,
    )
    assert evaluate_relationship_direction(accepted, candidate, direction).orientation is RelationshipOrientation.REVERSE


def test_forward_only_rejects_reversed_endpoints():
    accepted = _relationship()
    candidate = _relationship(source=accepted.target, target=accepted.source)
    result = evaluate_relationship_direction(
        accepted, candidate, _direction(RelationshipDirectionMode.FORWARD_ONLY)
    )
    assert result.is_valid is False
    assert result.violations == (RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED,)


def test_forward_orientation_rejects_inverse_type():
    accepted = _relationship()
    result = evaluate_relationship_direction(
        accepted, _relationship(relationship_type=_inverse_type()), _direction()
    )
    assert result.violations == (RelationshipDirectionViolationCode.RELATIONSHIP_TYPE_MISMATCH,)


def test_reverse_orientation_rejects_forward_type_for_inverse_mode():
    accepted = _relationship()
    result = evaluate_relationship_direction(
        accepted,
        _relationship(source=accepted.target, target=accepted.source),
        _direction(),
    )
    assert result.violations == (RelationshipDirectionViolationCode.RELATIONSHIP_TYPE_MISMATCH,)


def test_unrelated_endpoints_are_rejected():
    accepted = _relationship()
    candidate = _relationship(target=_reference("schools", "school-2"))
    result = evaluate_relationship_direction(accepted, candidate, _direction())
    assert result.violations == (RelationshipDirectionViolationCode.ENDPOINT_ORIENTATION_MISMATCH,)


def test_runtime_mode_mismatch_is_rejected_even_when_forward():
    result = evaluate_relationship_direction(
        _relationship(), _relationship(runtime_mode="production"), _direction()
    )
    assert result.violations == (RelationshipDirectionViolationCode.RUNTIME_MODE_MISMATCH,)


def test_multiple_findings_are_deterministically_ordered():
    accepted = _relationship()
    candidate = _relationship(
        relationship_type=_inverse_type(), runtime_mode="production"
    )
    result = evaluate_relationship_direction(accepted, candidate, _direction())
    assert result.violations == (
        RelationshipDirectionViolationCode.RUNTIME_MODE_MISMATCH,
        RelationshipDirectionViolationCode.RELATIONSHIP_TYPE_MISMATCH,
    )


def test_assert_returns_orientation_for_valid_candidate():
    assert assert_relationship_direction(
        _relationship(), _relationship(), _direction()
    ) is RelationshipOrientation.FORWARD


def test_assert_raises_with_result_for_invalid_candidate():
    with pytest.raises(RelationshipDirectionViolation) as captured:
        assert_relationship_direction(
            _relationship(), _relationship(runtime_mode="production"), _direction()
        )
    assert captured.value.result.violations == (
        RelationshipDirectionViolationCode.RUNTIME_MODE_MISMATCH,
    )


def test_valid_result_cannot_raise_violation():
    with pytest.raises(ValueError):
        RelationshipDirectionViolation(RelationshipDirectionResult.forward())


def test_invalid_result_requires_findings():
    with pytest.raises(ValueError):
        RelationshipDirectionResult(RelationshipOrientation.INVALID)


def test_valid_result_rejects_findings():
    finding = RelationshipDirectionFinding(
        RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED, "not allowed"
    )
    with pytest.raises(ValueError):
        RelationshipDirectionResult(RelationshipOrientation.FORWARD, (finding,))


def test_duplicate_finding_codes_are_rejected():
    one = RelationshipDirectionFinding(
        RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED, "one"
    )
    two = RelationshipDirectionFinding(
        RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED, "two"
    )
    with pytest.raises(ValueError):
        RelationshipDirectionResult.invalid(one, two)


def test_finding_requires_non_empty_message():
    with pytest.raises(ValueError):
        RelationshipDirectionFinding(
            RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED, "  "
        )


def test_result_serialization_is_deterministic():
    finding = RelationshipDirectionFinding(
        RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED, "not allowed"
    )
    assert RelationshipDirectionResult.invalid(finding).to_dict() == {
        "is_valid": False,
        "orientation": "invalid",
        "violations": ["REVERSE_NOT_ALLOWED"],
        "findings": [{"code": "REVERSE_NOT_ALLOWED", "message": "not allowed"}],
    }


def test_relationship_id_does_not_change_direction_classification():
    result = evaluate_relationship_direction(
        _relationship(), _relationship(relationship_id="different-view-id"), _direction()
    )
    assert result.orientation is RelationshipOrientation.FORWARD


def test_non_identity_type_metadata_does_not_change_semantic_match():
    candidate_type = RelationshipType(
        "school.enrolled_at", "SCHOOL.ENROLLED_AT", "Different display name"
    )
    result = evaluate_relationship_direction(
        _relationship(), _relationship(relationship_type=candidate_type), _direction()
    )
    assert result.is_valid is True


def test_reference_metadata_is_not_embedded_or_resolved():
    accepted = _relationship()
    candidate = _relationship(source=accepted.source, target=accepted.target)
    assert evaluate_relationship_direction(accepted, candidate, _direction()).is_valid


def test_accepted_relationship_must_match_direction_forward_type():
    with pytest.raises(RelationshipDirectionRuleError):
        evaluate_relationship_direction(
            _relationship(relationship_type=_inverse_type()),
            _relationship(relationship_type=_inverse_type()),
            _direction(),
        )


@pytest.mark.parametrize(
    "position,value",
    [
        ("accepted", object()),
        ("candidate", object()),
        ("direction", object()),
    ],
)
def test_input_types_are_checked(position, value):
    arguments = {
        "accepted": _relationship(),
        "candidate": _relationship(),
        "direction": _direction(),
    }
    arguments[position] = value
    with pytest.raises(TypeError):
        evaluate_relationship_direction(**arguments)


def test_result_requires_tuple_findings():
    with pytest.raises(TypeError):
        RelationshipDirectionResult(RelationshipOrientation.INVALID, [])


def test_result_requires_orientation_enum():
    with pytest.raises(TypeError):
        RelationshipDirectionResult("forward")


def test_finding_requires_code_enum():
    with pytest.raises(TypeError):
        RelationshipDirectionFinding("REVERSE_NOT_ALLOWED", "message")
