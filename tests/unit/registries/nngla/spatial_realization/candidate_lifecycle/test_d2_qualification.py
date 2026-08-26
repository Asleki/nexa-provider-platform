import pytest
from registries.nngla.spatial_realization.candidate_lifecycle.contracts import CandidateLifecycleStatus
from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from registries.nngla.spatial_realization.candidate_lifecycle.qualification import CandidateQualificationError,qualify_package
from ._support import assigned_preview,unresolved_preview,bound_governance


def test_independent_qualifier_can_qualify_exact_local_candidate_but_author_cannot():
    preview,fd,bd=assigned_preview()
    decisions=bound_governance(preview,fd,bd)
    p=build_candidate_package(preview,runtime_mode="production",author_actor_id="author",decisions=decisions)
    with pytest.raises(CandidateQualificationError): qualify_package(p,preview,qualifier_actor_id="author")
    q=qualify_package(p,preview,qualifier_actor_id="qualifier")
    assert q.status is CandidateLifecycleStatus.CANDIDATE_QUALIFIED
    assert q.symmetric_difference_m2==0.0 and q.positive_overlap_m2==0.0


def test_unresolved_candidate_cannot_be_qualified():
    preview=unresolved_preview()
    p=build_candidate_package(preview,runtime_mode="production",author_actor_id="author")
    with pytest.raises(CandidateQualificationError): qualify_package(p,preview,qualifier_actor_id="qualifier")
