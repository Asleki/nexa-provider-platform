from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from registries.relationships.constraint_contract import RelationshipConstraint
from registries.relationships.direction_contract import RelationshipDirection, RelationshipDirectionMode
from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_api_contract import (
    RelationshipApiContract,
    RelationshipApiContractError,
    RelationshipApiFinding,
    RelationshipApiOperation,
    RelationshipApiResultError,
    RelationshipApiSubsystem,
    RelationshipApiValidationError,
    RelationshipValidationRequest,
    RelationshipValidationResult,
)
from registries.relationships.relationship_constraint_rules import RelationshipConstraintContext
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_type import RelationshipType

NOW = datetime(2026, 7, 29, 16, 0, tzinfo=timezone.utc)


def rtype():
    return RelationshipType("type-1", "EDUCATION.ENROLLED_AT", "Enrolled At")


def relationship(**changes):
    values = dict(
        relationship_id="rel-1",
        relationship_type=rtype(),
        source=RegistryReference("students", "student-1"),
        target=RegistryReference("schools", "school-1"),
        runtime_mode="simulation",
    )
    values.update(changes)
    return RelationshipDefinition(**values)


def direction():
    return RelationshipDirection("dir-1", "DIRECTION.ENROLLED_AT", RelationshipDirectionMode.FORWARD_ONLY, rtype())


def constraint():
    return RelationshipConstraint(
        constraint_id="constraint-1",
        constraint_code="CONSTRAINT.ENROLLED_AT",
        relationship_type=rtype(),
        allowed_source_registry_ids=("students",),
        allowed_target_registry_ids=("schools",),
        runtime_modes=("simulation",),
    )


def provenance():
    return RelationshipProvenance(
        provenance_id="prov-1",
        relationship_id="rel-1",
        relationship_version=1,
        runtime_mode="simulation",
        source_type="system",
        source_system="nexilabs",
        recorded_at=NOW,
    )


def request(**changes):
    values = dict(
        request_id="req-1",
        relationship=relationship(),
        direction=direction(),
        constraint=constraint(),
        constraint_context=RelationshipConstraintContext(),
        provenance=provenance(),
        requested_at=NOW,
    )
    values.update(changes)
    return RelationshipValidationRequest(**values)


def test_operation_parse_and_contract_defaults():
    assert RelationshipApiOperation.parse(" VALIDATE ") is RelationshipApiOperation.VALIDATE
    contract = RelationshipApiContract()
    assert contract.supports("validate")
    assert contract.to_dict() == {"name": "relationship", "version": 1, "operations": ["validate"]}


def test_contract_round_trip():
    contract = RelationshipApiContract.from_dict(RelationshipApiContract().to_dict())
    assert contract == RelationshipApiContract()


def test_contract_rejects_invalid_version_and_duplicate_operations():
    with pytest.raises(RelationshipApiContractError):
        RelationshipApiContract(version=0)
    with pytest.raises(RelationshipApiContractError):
        RelationshipApiContract(operations=(RelationshipApiOperation.VALIDATE, RelationshipApiOperation.VALIDATE))


def test_contract_supports_returns_false_for_unknown():
    assert not RelationshipApiContract().supports("create")


def test_request_normalises_timestamp_and_metadata_deeply():
    local = NOW.astimezone(timezone(timedelta(hours=2)))
    payload = request(requested_at=local, metadata={"scenario": {"ids": [1, 2]}})
    assert payload.requested_at == NOW
    assert payload.metadata["scenario"]["ids"] == (1, 2)
    with pytest.raises(TypeError):
        payload.metadata["x"] = 1


def test_request_is_frozen():
    payload = request()
    with pytest.raises(FrozenInstanceError):
        payload.request_id = "changed"


@pytest.mark.parametrize(
    "field,bad",
    [
        ("relationship", object()),
        ("direction", object()),
        ("constraint", object()),
        ("constraint_context", object()),
        ("provenance", object()),
        ("existing_relationship", object()),
    ],
)
def test_request_validates_nested_types(field, bad):
    with pytest.raises(TypeError):
        request(**{field: bad})


def test_request_rejects_naive_timestamp_and_bad_id():
    with pytest.raises(RelationshipApiValidationError):
        request(requested_at=datetime(2026, 1, 1))
    with pytest.raises(RelationshipApiValidationError):
        request(request_id="bad id")


def test_request_round_trip_with_existing_relationship():
    original = request(existing_relationship=relationship(), metadata={"batch": ["a"]})
    restored = RelationshipValidationRequest.from_dict(original.to_dict())
    assert restored == original
    restored_dict = restored.to_dict()
    restored_dict["metadata"]["batch"].append("b")
    assert restored.metadata["batch"] == ("a",)


def test_request_from_dict_rejects_unknown_and_missing_fields():
    data = request().to_dict()
    data["extra"] = 1
    with pytest.raises(RelationshipApiValidationError):
        RelationshipValidationRequest.from_dict(data)
    data = request().to_dict()
    del data["relationship"]
    with pytest.raises(RelationshipApiValidationError):
        RelationshipValidationRequest.from_dict(data)


def test_finding_normalises_and_round_trips():
    finding = RelationshipApiFinding("constraint", " CODE ", " message ")
    assert finding.to_dict() == {"subsystem": "constraint", "code": "CODE", "message": "message"}
    assert RelationshipApiFinding.from_dict(finding.to_dict()) == finding


def test_finding_rejects_invalid_subsystem_or_empty_values():
    with pytest.raises(RelationshipApiResultError):
        RelationshipApiFinding("other", "X", "message")
    with pytest.raises(RelationshipApiResultError):
        RelationshipApiFinding("constraint", " ", "message")


def test_valid_result_and_invalid_result_contracts():
    valid = RelationshipValidationResult.valid(request_id="req-1", completed_at=NOW)
    assert valid.is_valid and valid.findings == ()
    finding = RelationshipApiFinding("constraint", "X", "bad")
    invalid = RelationshipValidationResult.invalid(request_id="req-1", completed_at=NOW, findings=(finding,))
    assert not invalid.is_valid


def test_result_rejects_inconsistent_validity():
    finding = RelationshipApiFinding("constraint", "X", "bad")
    with pytest.raises(RelationshipApiResultError):
        RelationshipValidationResult("req-1", NOW, True, (finding,))
    with pytest.raises(RelationshipApiResultError):
        RelationshipValidationResult("req-1", NOW, False)


def test_result_uniqueness_uses_subsystem_and_code():
    first = RelationshipApiFinding("constraint", "RUNTIME_MODE_MISMATCH", "a")
    second = RelationshipApiFinding("provenance", "RUNTIME_MODE_MISMATCH", "b")
    result = RelationshipValidationResult.invalid(request_id="req-1", completed_at=NOW, findings=(first, second))
    assert len(result.findings) == 2
    with pytest.raises(RelationshipApiResultError):
        RelationshipValidationResult.invalid(request_id="req-1", completed_at=NOW, findings=(first, first))


def test_result_round_trip_and_detachment():
    finding = RelationshipApiFinding("constraint", "X", "bad")
    original = RelationshipValidationResult.invalid(
        request_id="req-1", completed_at=NOW, findings=(finding,), metadata={"trace": [1]}
    )
    restored = RelationshipValidationResult.from_dict(original.to_dict())
    assert restored == original
    data = restored.to_dict()
    data["metadata"]["trace"].append(2)
    assert restored.metadata["trace"] == (1,)


def test_result_rejects_unknown_fields_and_naive_time():
    data = RelationshipValidationResult.valid(request_id="req-1", completed_at=NOW).to_dict()
    data["extra"] = True
    with pytest.raises(RelationshipApiResultError):
        RelationshipValidationResult.from_dict(data)
    with pytest.raises(RelationshipApiResultError):
        RelationshipValidationResult.valid(request_id="req-1", completed_at=datetime(2026, 1, 1))
