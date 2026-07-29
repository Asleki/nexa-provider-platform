from datetime import datetime, timezone

import pytest

from registries.relationships.constraint_contract import (
    RelationshipCardinality,
    RelationshipConstraint,
    RelationshipDuplicatePolicy,
    RelationshipSelfReferencePolicy,
)
from registries.relationships.direction_contract import RelationshipDirection, RelationshipDirectionMode
from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_api_contract import (
    RelationshipApiContract,
    RelationshipApiFinding,
    RelationshipApiOperation,
    RelationshipApiSubsystem,
    RelationshipValidationRequest,
    RelationshipValidationResult,
)
from registries.relationships.relationship_constraint_rules import RelationshipConstraintContext
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType
from registries.relationships.relationship_validation_api import (
    RelationshipApiExecutionError,
    RelationshipValidationApi,
    RelationshipValidationViolation,
    assert_relationship_validation,
    validate_relationship,
)

NOW = datetime(2026, 7, 29, 17, 0, tzinfo=timezone.utc)


def rtype(code="EDUCATION.ENROLLED_AT", type_id="type-1"):
    return RelationshipType(type_id, code, "Relationship")


def rel(**changes):
    values = dict(
        relationship_id="rel-1",
        relationship_type=rtype(),
        source=RegistryReference("students", "student-1"),
        target=RegistryReference("schools", "school-1"),
        runtime_mode="simulation",
        version=1,
    )
    values.update(changes)
    return RelationshipDefinition(**values)


def direction(**changes):
    values = dict(
        direction_id="dir-1",
        direction_code="DIRECTION.ENROLLED_AT",
        mode=RelationshipDirectionMode.FORWARD_ONLY,
        forward_type=rtype(),
    )
    values.update(changes)
    return RelationshipDirection(**values)


def constraint(**changes):
    values = dict(
        constraint_id="constraint-1",
        constraint_code="CONSTRAINT.ENROLLED_AT",
        relationship_type=rtype(),
        allowed_source_registry_ids=("students",),
        allowed_target_registry_ids=("schools",),
        source_cardinality=RelationshipCardinality(0, 1),
        target_cardinality=RelationshipCardinality(0, None),
        self_reference_policy=RelationshipSelfReferencePolicy.PROHIBIT,
        duplicate_policy=RelationshipDuplicatePolicy.PROHIBIT,
        runtime_modes=("simulation",),
    )
    values.update(changes)
    return RelationshipConstraint(**values)


def provenance(**changes):
    values = dict(
        provenance_id="prov-1",
        relationship_id="rel-1",
        relationship_version=1,
        runtime_mode="simulation",
        source_type="system",
        source_system="nexilabs",
        recorded_at=NOW,
    )
    values.update(changes)
    return RelationshipProvenance(**values)


def request(**changes):
    values = dict(
        request_id="req-1",
        relationship=rel(),
        direction=direction(),
        constraint=constraint(),
        constraint_context=RelationshipConstraintContext(),
        provenance=provenance(),
        requested_at=NOW,
    )
    values.update(changes)
    return RelationshipValidationRequest(**values)


def fixed_api(**changes):
    return RelationshipValidationApi(clock=lambda: NOW, **changes)


def test_valid_package_returns_validation_only_result():
    result = fixed_api().validate(request())
    assert result.is_valid
    assert result.completed_at == NOW
    assert result.metadata == {"validation_only": True, "persisted": False, "approved": False}


def test_execute_alias_matches_validate():
    api = fixed_api()
    assert api.execute(request()) == api.validate(request())


def test_convenience_function_and_assertion_success():
    assert validate_relationship(request(), clock=lambda: NOW).is_valid
    assert assert_relationship_validation(request(), clock=lambda: NOW).is_valid


def test_optional_immutable_comparison_is_skipped():
    assert fixed_api().validate(request(existing_relationship=None)).is_valid


def test_compatible_existing_relationship_passes():
    assert fixed_api().validate(request(existing_relationship=rel())).is_valid


def test_immutable_change_is_reported_first():
    existing = rel(relationship_id="rel-old")
    result = fixed_api().validate(request(existing_relationship=existing))
    assert not result.is_valid
    assert result.findings[0].subsystem is RelationshipApiSubsystem.IMMUTABLE_REFERENCE
    assert result.findings[0].code == "RELATIONSHIP_ID_CHANGED"


def test_direction_type_mismatch_becomes_finding_not_execution_error():
    wrong = direction(forward_type=rtype("EDUCATION.TEACHES", "type-2"))
    result = fixed_api().validate(request(direction=wrong))
    assert any(f.subsystem is RelationshipApiSubsystem.DIRECTION and f.code == "RELATIONSHIP_TYPE_MISMATCH" for f in result.findings)


def test_constraint_type_mismatch():
    wrong = constraint(relationship_type=rtype("EDUCATION.TEACHES", "type-2"))
    result = fixed_api().validate(request(constraint=wrong))
    assert [(f.subsystem.value, f.code) for f in result.findings] == [("constraint", "RELATIONSHIP_TYPE_MISMATCH")]


def test_constraint_runtime_and_endpoint_findings():
    candidate = rel(
        source=RegistryReference("citizens", "cit-1"),
        target=RegistryReference("banks", "bank-1"),
        runtime_mode="production",
    )
    prov = provenance(runtime_mode="production")
    result = fixed_api().validate(request(relationship=candidate, provenance=prov))
    codes = [(f.subsystem.value, f.code) for f in result.findings]
    assert codes == [
        ("constraint", "RUNTIME_MODE_NOT_ALLOWED"),
        ("constraint", "SOURCE_REGISTRY_NOT_ALLOWED"),
        ("constraint", "TARGET_REGISTRY_NOT_ALLOWED"),
    ]


def test_self_reference_duplicate_and_cardinality_findings():
    same = RegistryReference("students", "student-1")
    candidate = rel(source=same, target=same)
    broad = constraint(allowed_target_registry_ids=("students",))
    context = RelationshipConstraintContext(existing_source_count=1, existing_pair_count=1)
    result = fixed_api().validate(request(relationship=candidate, constraint=broad, constraint_context=context))
    assert [f.code for f in result.findings] == [
        "SELF_REFERENCE_PROHIBITED",
        "DUPLICATE_PAIR_PROHIBITED",
        "SOURCE_CARDINALITY_EXCEEDED",
    ]


def test_target_cardinality_finding():
    limited = constraint(target_cardinality=RelationshipCardinality(0, 1))
    context = RelationshipConstraintContext(existing_target_count=1)
    result = fixed_api().validate(request(constraint=limited, constraint_context=context))
    assert [f.code for f in result.findings] == ["TARGET_CARDINALITY_EXCEEDED"]


def test_provenance_all_mismatches():
    bad = provenance(relationship_id="rel-2", relationship_version=2, runtime_mode="production")
    result = fixed_api().validate(request(provenance=bad))
    assert [(f.subsystem.value, f.code) for f in result.findings] == [
        ("provenance", "RELATIONSHIP_ID_MISMATCH"),
        ("provenance", "RELATIONSHIP_VERSION_MISMATCH"),
        ("provenance", "RUNTIME_MODE_MISMATCH"),
    ]


def test_findings_are_aggregated_in_milestone_order():
    existing = rel(relationship_id="old-rel")
    wrong_direction = direction(forward_type=rtype("EDUCATION.TEACHES", "type-2"))
    wrong_constraint = constraint(relationship_type=rtype("EDUCATION.TEACHES", "type-2"))
    bad_provenance = provenance(runtime_mode="production")
    result = fixed_api().validate(
        request(
            existing_relationship=existing,
            direction=wrong_direction,
            constraint=wrong_constraint,
            provenance=bad_provenance,
        )
    )
    assert [f.subsystem for f in result.findings] == [
        RelationshipApiSubsystem.IMMUTABLE_REFERENCE,
        RelationshipApiSubsystem.DIRECTION,
        RelationshipApiSubsystem.CONSTRAINT,
        RelationshipApiSubsystem.PROVENANCE,
    ]


def test_same_code_can_exist_in_distinct_subsystems():
    candidate = rel(runtime_mode="production")
    bad_provenance = provenance(runtime_mode="simulation")
    result = fixed_api().validate(request(relationship=candidate, provenance=bad_provenance))
    matches = [f for f in result.findings if "RUNTIME_MODE" in f.code]
    assert len(matches) == 2
    assert {f.subsystem for f in matches} == {RelationshipApiSubsystem.CONSTRAINT, RelationshipApiSubsystem.PROVENANCE}


def test_assertion_raises_complete_structured_result():
    with pytest.raises(RelationshipValidationViolation) as captured:
        fixed_api().assert_valid(request(provenance=provenance(runtime_mode="production")))
    assert captured.value.result.findings[0].code == "RUNTIME_MODE_MISMATCH"


def test_violation_rejects_valid_result_and_wrong_type():
    valid = RelationshipValidationResult.valid(request_id="req-1", completed_at=NOW)
    with pytest.raises(ValueError):
        RelationshipValidationViolation(valid)
    with pytest.raises(TypeError):
        RelationshipValidationViolation("bad")


def test_invalid_request_type_is_execution_type_error():
    with pytest.raises(TypeError):
        fixed_api().validate(object())


def test_contract_type_and_clock_type_are_checked():
    with pytest.raises(TypeError):
        RelationshipValidationApi(contract=object())
    with pytest.raises(TypeError):
        RelationshipValidationApi(clock=object())


def test_contract_must_support_operation():
    contract = RelationshipApiContract(operations=(RelationshipApiOperation.VALIDATE,))
    assert fixed_api(contract=contract).validate(request()).is_valid


def test_clock_must_return_aware_datetime():
    with pytest.raises(RelationshipApiExecutionError):
        RelationshipValidationApi(clock=lambda: "now").validate(request())
    with pytest.raises(RelationshipApiExecutionError):
        RelationshipValidationApi(clock=lambda: datetime(2026, 1, 1)).validate(request())


def test_inputs_are_not_mutated():
    payload = request(metadata={"scenario": ["x"]})
    before = payload.to_dict()
    fixed_api().validate(payload)
    assert payload.to_dict() == before


def test_no_persistence_or_event_claims_in_result():
    result = fixed_api().validate(request())
    data = result.to_dict()
    assert data["metadata"]["persisted"] is False
    assert data["metadata"]["approved"] is False
    assert "events" not in data
    assert "receipt" not in data
