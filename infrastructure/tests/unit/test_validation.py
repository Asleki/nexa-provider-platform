from infrastructure.governance.validation import *
from infrastructure.ingestion.pipelines import CandidateEnvelope
def c(cid,p): return CandidateEnvelope(cid,1,"source:file",p)
def test_validation_passes_clean_candidate():
    engine=ValidationEngine((RequiredFieldsRule("dataset_id"),NamespacedIdentifierRule("dataset_id")))
    receipt=engine.validate((c("candidate:1",{"dataset_id":"dataset:one"}),),ValidationContext("rules:generic",1,"production"),"validation:1")
    assert receipt.outcome is ValidationOutcome.passed
def test_duplicate_is_quarantined():
    engine=ValidationEngine((DuplicateCandidateRule(),))
    receipt=engine.validate((c("candidate:1",{"x":1}),c("candidate:2",{"x":1})),ValidationContext("rules:generic",1,"production"))
    assert receipt.outcome is ValidationOutcome.quarantined
def test_findings_are_deterministic():
    engine=ValidationEngine((RequiredFieldsRule("z","a"),))
    r=engine.validate((c("candidate:1",{}),),ValidationContext("rules:generic",1,"production"),"validation:fixed")
    assert [f.message for f in r.findings]==sorted(f.message for f in r.findings)
