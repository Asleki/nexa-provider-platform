import pytest
from registries.nngla.spatial_realization.candidate_lifecycle.contracts import CandidateRuntime,GovernedDecisionRecord


def test_distinct_reviewer_approver_and_exact_run_scope_are_contractual():
    with pytest.raises(ValueError):
        GovernedDecisionRecord(
            "fabric-decision:nngla:"+"a"*64,
            "fabric-run:nngla:"+"b"*64,
            "c"*64,
            "FACE_ASSIGNMENT","fabric-face:nngla:x","d"*64,
            "NG-ADM-000001","GOVERNED_REVIEW","REF","why","actor","actor",CandidateRuntime.PRODUCTION,
        )
