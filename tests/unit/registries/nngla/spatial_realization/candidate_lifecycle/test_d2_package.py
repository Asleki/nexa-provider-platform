import pytest
from dataclasses import replace
from registries.nngla.spatial_realization.candidate_lifecycle.contracts import CandidateLifecycleStatus,CandidateRuntime
from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from ._support import unresolved_preview,assigned_preview,bound_governance


def test_unresolved_northgate_is_durable_governance_required():
    p=build_candidate_package(unresolved_preview(),runtime_mode=CandidateRuntime.PRODUCTION,author_actor_id="author")
    assert p.lifecycle_status is CandidateLifecycleStatus.GOVERNANCE_REQUIRED
    assert p.parent_administrative_area_id=="NG-ADM-000032"
    assert len(p.edges)==59 and len(p.faces)==10
    assert p.assignment_sha256=="" and p.sibling_candidates==()


def test_assigned_northgate_is_ready_and_deterministic():
    preview,fd,bd=assigned_preview()
    decisions=bound_governance(preview,fd,bd)
    a=build_candidate_package(preview,runtime_mode="production",author_actor_id="author",decisions=decisions)
    b=build_candidate_package(preview,runtime_mode="production",author_actor_id="author",decisions=tuple(reversed(decisions)))
    assert a.fabric_run_id==b.fabric_run_id
    assert a.package_sha256==b.package_sha256
    assert a.lifecycle_status is CandidateLifecycleStatus.READY_FOR_CANDIDATE_QUALIFICATION
    assert len(a.sibling_candidates)==8


def test_package_rejects_decision_from_foreign_run():
    preview,fd,bd=assigned_preview()
    decisions=bound_governance(preview,fd,bd)
    foreign=replace(decisions[0],fabric_run_id="fabric-run:nngla:"+"f"*64)
    with pytest.raises(ValueError,match="different fabric run or scope"):
        build_candidate_package(preview,runtime_mode="production",author_actor_id="author",decisions=(foreign,)+decisions[1:])
