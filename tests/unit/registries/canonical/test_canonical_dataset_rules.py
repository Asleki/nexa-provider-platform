from datetime import datetime, timezone
import pytest
from registries.canonical import CanonicalDatasetDefinition, CanonicalDatasetReference, CanonicalDatasetRules, CanonicalDatasetType
TYPE = CanonicalDatasetType("type.derived", "DATASET.DERIVED", "Derived")
def make(**overrides):
    values=dict(dataset_id="dataset.output",dataset_code="DATASET.OUTPUT",dataset_name="Output",dataset_type=TYPE,authority_registry_id="registry.people",record_type_code="IDENTITY.PERSON",schema_id="schema.person",schema_version=1,dataset_version=1,runtime_mode="simulation",created_at=datetime(2026,7,29,tzinfo=timezone.utc))
    values.update(overrides); return CanonicalDatasetDefinition(**values)
def test_valid_definition_has_no_findings():
    assert CanonicalDatasetRules.validate(make(source_datasets=[CanonicalDatasetReference("dataset.seed",1,"simulation")])).is_valid
def test_runtime_mismatch_is_reported_not_mutated():
    value=make(source_datasets=[CanonicalDatasetReference("dataset.seed",1,"production")]); result=CanonicalDatasetRules.validate(value)
    assert not result.is_valid and result.findings[0].code=="CANONICAL_DATASET_RUNTIME_MISMATCH"
    assert value.source_datasets[0].runtime_mode=="production"
def test_other_version_of_same_identity_is_cycle_risk():
    result=CanonicalDatasetRules.validate(make(dataset_version=2,source_datasets=[CanonicalDatasetReference("dataset.output",1,"simulation")]))
    assert any(f.code=="CANONICAL_DATASET_LINEAGE_CYCLE_RISK" for f in result.findings)
def test_result_serialises_deterministically():
    data=CanonicalDatasetRules.validate(make()).to_dict(); assert data=={"is_valid":True,"findings":[]}
def test_wrong_type_rejected():
    with pytest.raises(TypeError): CanonicalDatasetRules.validate(object())
