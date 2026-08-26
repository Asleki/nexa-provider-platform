from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from registries.nngla.spatial_realization.candidate_lifecycle.contracts import CandidateLifecycleStatus
from registries.nngla.spatial_realization.shared_face_preview import build_read_only_shared_face_preview


def test_real_northgate_and_nyara_cases_remain_fail_closed_without_real_governance():
    n=build_candidate_package(build_read_only_shared_face_preview('NG-PLC-000086'),runtime_mode='production',author_actor_id='verification')
    s=build_candidate_package(build_read_only_shared_face_preview('NG-PLC-000258',material_rule_codes=('CITY_PARENT_CONTAINMENT_FAILED','CITY_DISTRICT_OVERSHOOT')),runtime_mode='production',author_actor_id='verification')
    assert n.lifecycle_status is CandidateLifecycleStatus.GOVERNANCE_REQUIRED
    assert s.lifecycle_status is CandidateLifecycleStatus.GOVERNANCE_REQUIRED
    assert not n.sibling_candidates and not s.sibling_candidates
