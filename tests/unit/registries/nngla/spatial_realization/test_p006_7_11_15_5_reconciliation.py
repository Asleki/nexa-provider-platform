from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.contracts import ReconciliationAction,TopologyAssessment
from registries.nngla.spatial_realization.persistence import MemorySpatialRealizationRepository
from registries.nngla.spatial_realization.reconciliation import reconcile_assessment,reconcile_candidate


def test_pristine_selected_root_is_create_new_without_requiring_other_699_places():
    repo=MemorySpatialRealizationRepository();closure=build_city_closure('NG-PLC-000001');snapshot=repo.snapshot((closure,))
    assessment=TopologyAssessment(closure.root.place_id,closure.desired_candidates,())
    items=reconcile_assessment(closure,assessment,snapshot)
    assert {i.action for i in items}=={ReconciliationAction.CREATE_NEW}
    assert len(items)==11


def test_exact_existing_geometry_can_be_associated_then_reused():
    repo=MemorySpatialRealizationRepository();closure=build_city_closure('NG-PLC-000001');candidate=closure.place_reference
    gid=repo.seed_candidate(candidate,associate=False)
    item=reconcile_candidate(candidate,repo.snapshot((closure,)))
    assert item.action is ReconciliationAction.ASSOCIATE_EXISTING and item.existing_geometry_id==gid
    repo.associate(candidate,gid)
    item=reconcile_candidate(candidate,repo.snapshot((closure,)))
    assert item.action is ReconciliationAction.REUSE_EXISTING


def test_conflicting_active_geometry_fails_closed():
    from dataclasses import replace
    repo=MemorySpatialRealizationRepository();closure=build_city_closure('NG-PLC-000001');candidate=closure.place_reference
    wrong=replace(candidate,checksum_sha256='f'*64,source_candidate_id='wrong')
    repo.seed_candidate(wrong,associate=True)
    item=reconcile_candidate(candidate,repo.snapshot((closure,)))
    assert item.action is ReconciliationAction.BLOCKED
