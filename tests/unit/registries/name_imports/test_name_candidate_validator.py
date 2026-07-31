from datetime import datetime,timezone
from registries.name_imports.name_candidate import NameCandidate
from registries.name_imports.name_candidate_validator import NameCandidateValidator

def make(name="Alex",source_reference="dataset:1",runtime="simulation"):
    return NameCandidate("candidate:1","batch:1","source:1",2,name,"first_name",runtime,source_reference=source_reference,created_at=datetime(2026,1,1,tzinfo=timezone.utc))

def test_valid_candidate_has_no_findings():
    result=NameCandidateValidator().validate(make(),batch_runtime_mode="simulation").result
    assert result.valid and not result.messages

def test_empty_name_and_runtime_mismatch_are_errors():
    result=NameCandidateValidator().validate(make("",runtime="simulation"),batch_runtime_mode="production").result
    assert not result.valid
    assert [m.code for m in result.errors]==["NAME_IMPORT_EMPTY_NAME","NAME_IMPORT_RUNTIME_MISMATCH"]

def test_normalization_and_missing_source_are_warnings_in_deterministic_order():
    result=NameCandidateValidator().validate(make("Alex   John",None)).result
    assert result.valid
    assert [m.code for m in result.warnings]==["NAME_IMPORT_NORMALIZED","NAME_IMPORT_SOURCE_REFERENCE_MISSING"]
