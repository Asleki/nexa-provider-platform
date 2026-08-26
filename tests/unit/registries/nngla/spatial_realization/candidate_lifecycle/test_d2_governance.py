import pytest
from registries.nngla.spatial_realization.candidate_lifecycle.contracts import CandidateRuntime
from registries.nngla.spatial_realization.candidate_lifecycle.governance import CandidateGovernanceError,bind_governance_decisions
from registries.nngla.spatial_realization.contracts import FaceAssignmentDecision,FaceDecisionKind


def _decision():
    return FaceAssignmentDecision("fabric-face:nngla:x","a"*64,"NG-ADM-000001",FaceDecisionKind.TEST_ONLY_GOVERNANCE_FIXTURE,"TEST-ONLY:1","fixture")


def test_production_rejects_test_only_governance():
    with pytest.raises(CandidateGovernanceError):
        bind_governance_decisions(
            fabric_run_id="fabric-run:nngla:"+"b"*64,
            scope_fingerprint="c"*64,
            face_decisions=(_decision(),),reviewer_actor_id="r",approver_actor_id="a",runtime_mode=CandidateRuntime.PRODUCTION,
        )


def test_decision_identity_is_bound_to_exact_run_and_scope():
    d=FaceAssignmentDecision("fabric-face:nngla:x","a"*64,"NG-ADM-000001",FaceDecisionKind.GOVERNED_REVIEW,"REF","fixture")
    a=bind_governance_decisions(fabric_run_id="fabric-run:nngla:"+"b"*64,scope_fingerprint="c"*64,face_decisions=(d,),reviewer_actor_id="r",approver_actor_id="a",runtime_mode="simulation")[0]
    b=bind_governance_decisions(fabric_run_id="fabric-run:nngla:"+"d"*64,scope_fingerprint="c"*64,face_decisions=(d,),reviewer_actor_id="r",approver_actor_id="a",runtime_mode="simulation")[0]
    c=bind_governance_decisions(fabric_run_id="fabric-run:nngla:"+"b"*64,scope_fingerprint="e"*64,face_decisions=(d,),reviewer_actor_id="r",approver_actor_id="a",runtime_mode="simulation")[0]
    assert len({a.decision_id,b.decision_id,c.decision_id})==3
