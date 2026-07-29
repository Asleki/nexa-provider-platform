from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from registries.relationships.immutable_reference_result import (
    ImmutableReferenceField,
    ImmutableReferenceFinding,
    ImmutableReferenceResult,
    ImmutableReferenceViolationCode,
)


def finding(field=ImmutableReferenceField.RECORD_ID):
    return ImmutableReferenceFinding(
        ImmutableReferenceViolationCode.RECORD_ID_CHANGED,
        field,
        "old",
        "new",
    )


def test_compatible_result_has_no_findings():
    result = ImmutableReferenceResult.compatible()
    assert result.is_compatible is True
    assert result.findings == ()
    assert result.changed_fields == ()
    assert result.violations == ()


def test_result_orders_findings_by_contract_field_order():
    result = ImmutableReferenceResult.from_findings(
        [
            ImmutableReferenceFinding(
                ImmutableReferenceViolationCode.RUNTIME_MODE_CHANGED,
                ImmutableReferenceField.RUNTIME_MODE,
                "simulation",
                "production",
            ),
            finding(ImmutableReferenceField.RECORD_ID),
            ImmutableReferenceFinding(
                ImmutableReferenceViolationCode.REGISTRY_ID_CHANGED,
                ImmutableReferenceField.REGISTRY_ID,
                "a.registry",
                "b.registry",
            ),
        ]
    )
    assert result.changed_fields == (
        ImmutableReferenceField.REGISTRY_ID,
        ImmutableReferenceField.RECORD_ID,
        ImmutableReferenceField.RUNTIME_MODE,
    )


def test_result_rejects_duplicate_fields():
    with pytest.raises(ValueError, match="at most one result"):
        ImmutableReferenceResult((finding(), finding()))


def test_result_requires_typed_findings_and_tuple_storage():
    with pytest.raises(TypeError, match="tuple"):
        ImmutableReferenceResult([])
    with pytest.raises(TypeError, match="ImmutableReferenceFinding"):
        ImmutableReferenceResult((object(),))


def test_finding_requires_typed_code_and_field():
    with pytest.raises(TypeError, match="ViolationCode"):
        ImmutableReferenceFinding("RECORD_ID_CHANGED", ImmutableReferenceField.RECORD_ID, 1, 2)
    with pytest.raises(TypeError, match="ImmutableReferenceField"):
        ImmutableReferenceFinding(ImmutableReferenceViolationCode.RECORD_ID_CHANGED, "record_id", 1, 2)


def test_result_and_finding_are_frozen():
    result = ImmutableReferenceResult((finding(),))
    with pytest.raises(FrozenInstanceError):
        result.findings = ()
    with pytest.raises(FrozenInstanceError):
        result.findings[0].proposed_value = "another"


def test_result_serialization_is_deterministic_and_detached():
    result = ImmutableReferenceResult((finding(),))
    payload = result.to_dict()
    assert payload == {
        "is_compatible": False,
        "changed_fields": ["record_id"],
        "violations": ["RECORD_ID_CHANGED"],
        "findings": [
            {
                "code": "RECORD_ID_CHANGED",
                "field": "record_id",
                "existing_value": "old",
                "proposed_value": "new",
            }
        ],
    }
    payload["findings"].clear()
    assert len(result.findings) == 1


def test_findings_by_field_returns_read_only_index():
    result = ImmutableReferenceResult((finding(),))
    indexed = result.findings_by_field()
    assert isinstance(indexed, MappingProxyType)
    assert indexed[ImmutableReferenceField.RECORD_ID] == finding()
    with pytest.raises(TypeError):
        indexed[ImmutableReferenceField.REGISTRY_ID] = finding()


def test_from_findings_consumes_generator_without_retaining_it():
    result = ImmutableReferenceResult.from_findings(finding() for _ in range(1))
    assert result.findings == (finding(),)


@pytest.mark.parametrize("invalid", [None, 1, "finding", b"finding", {"finding": 1}])
def test_from_findings_rejects_non_finding_iterables_or_non_iterables(invalid):
    with pytest.raises(TypeError):
        ImmutableReferenceResult.from_findings(invalid)
