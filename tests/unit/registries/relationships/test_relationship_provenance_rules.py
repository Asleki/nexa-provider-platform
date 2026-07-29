from datetime import datetime, timezone

import pytest

from registries.relationships.provenance_contract import RelationshipProvenance
from registries.relationships.registry_reference import RegistryReference
from registries.relationships.relationship_definition import RelationshipDefinition
from registries.relationships.relationship_provenance_rules import (
    RelationshipProvenanceFinding,
    RelationshipProvenanceResult,
    RelationshipProvenanceViolation,
    RelationshipProvenanceViolationCode,
    assert_relationship_provenance,
    evaluate_relationship_provenance,
)
from registries.relationships.relationship_type import RelationshipType

NOW = datetime(2026, 7, 29, 13, 0, tzinfo=timezone.utc)


def relationship(**overrides):
    values = dict(
        relationship_id="rel-001",
        relationship_type=RelationshipType(
            relationship_type_id="type-1",
            relationship_type_code="EDUCATION.ENROLLED_AT",
            relationship_type_name="Enrolled At",
        ),
        source=RegistryReference(registry_id="citizens", record_id="cit-1"),
        target=RegistryReference(registry_id="schools", record_id="sch-1"),
        runtime_mode="simulation",
        version=2,
    )
    values.update(overrides)
    return RelationshipDefinition(**values)


def provenance(**overrides):
    values = dict(
        provenance_id="prov-1",
        relationship_id="rel-001",
        relationship_version=2,
        runtime_mode="simulation",
        source_type="system",
        source_system="nexilabs",
        recorded_at=NOW,
    )
    values.update(overrides)
    return RelationshipProvenance(**values)


def test_compatible_result():
    result = evaluate_relationship_provenance(relationship(), provenance())
    assert result.is_compatible
    assert result.violations == ()


def test_relationship_id_mismatch():
    result = evaluate_relationship_provenance(relationship(), provenance(relationship_id="rel-2"))
    assert result.violations == (RelationshipProvenanceViolationCode.RELATIONSHIP_ID_MISMATCH,)


def test_relationship_version_mismatch():
    result = evaluate_relationship_provenance(relationship(), provenance(relationship_version=1))
    assert result.violations == (RelationshipProvenanceViolationCode.RELATIONSHIP_VERSION_MISMATCH,)


def test_runtime_mode_mismatch():
    result = evaluate_relationship_provenance(relationship(), provenance(runtime_mode="production"))
    assert result.violations == (RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,)


def test_all_findings_are_reported_in_deterministic_order():
    result = evaluate_relationship_provenance(
        relationship(),
        provenance(relationship_id="rel-2", relationship_version=1, runtime_mode="production"),
    )
    assert result.violations == (
        RelationshipProvenanceViolationCode.RELATIONSHIP_ID_MISMATCH,
        RelationshipProvenanceViolationCode.RELATIONSHIP_VERSION_MISMATCH,
        RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
    )


def test_finding_normalises_message():
    finding = RelationshipProvenanceFinding(
        RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
        " mismatch ",
    )
    assert finding.message == "mismatch"


def test_finding_requires_code_enum():
    with pytest.raises(TypeError):
        RelationshipProvenanceFinding("RUNTIME_MODE_MISMATCH", "mismatch")


def test_finding_requires_non_empty_message():
    with pytest.raises(ValueError):
        RelationshipProvenanceFinding(
            RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
            " ",
        )


def test_result_requires_tuple():
    with pytest.raises(TypeError):
        RelationshipProvenanceResult([])


def test_result_rejects_non_finding():
    with pytest.raises(TypeError):
        RelationshipProvenanceResult(("bad",))


def test_result_rejects_duplicate_codes():
    first = RelationshipProvenanceFinding(
        RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
        "a",
    )
    second = RelationshipProvenanceFinding(
        RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
        "b",
    )
    with pytest.raises(ValueError):
        RelationshipProvenanceResult((first, second))


def test_compatible_constructor():
    assert RelationshipProvenanceResult.compatible().is_compatible


def test_from_findings_constructor():
    finding = RelationshipProvenanceFinding(
        RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
        "mismatch",
    )
    assert RelationshipProvenanceResult.from_findings(finding).findings == (finding,)


def test_result_serialisation():
    result = evaluate_relationship_provenance(relationship(), provenance(runtime_mode="production"))
    assert result.to_dict() == {
        "is_compatible": False,
        "violations": ["RUNTIME_MODE_MISMATCH"],
        "findings": [{"code": "RUNTIME_MODE_MISMATCH", "message": "provenance runtime_mode does not match the relationship runtime mode."}],
    }


def test_assert_success_returns_none():
    assert assert_relationship_provenance(relationship(), provenance()) is None


def test_assert_raises_structured_violation():
    with pytest.raises(RelationshipProvenanceViolation) as captured:
        assert_relationship_provenance(relationship(), provenance(runtime_mode="production"))
    assert captured.value.result.violations == (RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,)


def test_violation_rejects_compatible_result():
    with pytest.raises(ValueError):
        RelationshipProvenanceViolation(RelationshipProvenanceResult.compatible())


def test_violation_requires_result():
    with pytest.raises(TypeError):
        RelationshipProvenanceViolation("bad")

@pytest.mark.parametrize("bad", [None, object(), "relationship"])
def test_relationship_input_type_checked(bad):
    with pytest.raises(TypeError):
        evaluate_relationship_provenance(bad, provenance())

@pytest.mark.parametrize("bad", [None, object(), "provenance"])
def test_provenance_input_type_checked(bad):
    with pytest.raises(TypeError):
        evaluate_relationship_provenance(relationship(), bad)


def test_simulation_pair_is_compatible():
    assert evaluate_relationship_provenance(relationship(runtime_mode="simulation"), provenance(runtime_mode="simulation")).is_compatible


def test_production_pair_is_compatible():
    assert evaluate_relationship_provenance(relationship(runtime_mode="production"), provenance(runtime_mode="production")).is_compatible


def test_inputs_are_not_mutated():
    rel = relationship()
    prov = provenance()
    before_rel = rel.to_dict()
    before_prov = prov.to_dict()
    evaluate_relationship_provenance(rel, prov)
    assert rel.to_dict() == before_rel
    assert prov.to_dict() == before_prov
