import pytest
from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.contracts import FindingSeverity,FindingStatus,TopologyAssessment,TopologyFinding
from registries.nngla.spatial_realization.execution import SpatialRealizationExecutionError
from registries.nngla.spatial_realization.orchestration import GovernedSpatialBatchEngine
from registries.nngla.spatial_realization.persistence import MemorySpatialRealizationRepository
from registries.nngla.spatial_realization.preview import confirmation_token
from registries.nngla.spatial_realization.selection import eligible_city_root_ids
from registries.nngla.spatial_realization.topology import PassThroughTopologyEngine


class FailingRootTopology:
    def __init__(self,root):self.root=root
    def assess(self,closure):
        if closure.root.place_id!=self.root:return TopologyAssessment(closure.root.place_id,closure.desired_candidates,())
        f=TopologyFinding('finding:test',closure.root.place_id,'TEST_BLOCK',FindingSeverity.BLOCKING,FindingStatus.OPEN,closure.root.administrative_area_id)
        return TopologyAssessment(closure.root.place_id,closure.desired_candidates,(f,))


def test_orivane_reference_run_uses_generic_engine_and_exact_rerun_is_reused():
    repo=MemorySpatialRealizationRepository();engine=GovernedSpatialBatchEngine(repo,PassThroughTopologyEngine(),repository_revision='rev')
    p=engine.preview(['NG-PLC-000001']);token=confirmation_token(p.database_name,p.fingerprint)
    r=engine.execute(['NG-PLC-000001'],approved_fingerprint=p.fingerprint,confirmation=token,submitter_actor_id='submitter',approver_actor_id='approver')
    assert r.status=='APPLIED' and r.geometry_insert_count==11 and r.association_count==10
    r2=engine.execute(['NG-PLC-000001'],approved_fingerprint=p.fingerprint,confirmation=token,submitter_actor_id='submitter2',approver_actor_id='approver2')
    assert r2.status=='REUSED' and r2.replayed


def test_one_failed_root_blocks_entire_six_city_selection_before_any_geometry_id_is_consumed():
    roots=eligible_city_root_ids()[:6];repo=MemorySpatialRealizationRepository();before=repo.allocator._next
    engine=GovernedSpatialBatchEngine(repo,FailingRootTopology(roots[3]),repository_revision='rev')
    p=engine.preview(roots)
    assert not p.execution_ready
    with pytest.raises(SpatialRealizationExecutionError):
        engine.execute(roots,approved_fingerprint=p.fingerprint,confirmation=confirmation_token(p.database_name,p.fingerprint),submitter_actor_id='s',approver_actor_id='a')
    assert repo.allocator._next==before and not repo.geometries and all(v['geometry_reference'] is None for v in repo.places.values())


def test_mixed_realized_and_unrealized_roots_are_planned_without_pristine_global_baseline():
    roots=eligible_city_root_ids()[:2];repo=MemorySpatialRealizationRepository();engine=GovernedSpatialBatchEngine(repo,PassThroughTopologyEngine(),repository_revision='rev')
    p1=engine.preview([roots[0]]);engine.execute([roots[0]],approved_fingerprint=p1.fingerprint,confirmation=confirmation_token(p1.database_name,p1.fingerprint),submitter_actor_id='s1',approver_actor_id='a1')
    p2=engine.preview(roots)
    assert p2.execution_ready
    actions={(i.root_place_id,i.action.value) for i in p2.reconciliation}
    assert (roots[0],'REUSE_EXISTING') in actions and (roots[1],'CREATE_NEW') in actions


def test_reused_execution_still_requires_exact_confirmation_token():
    repo=MemorySpatialRealizationRepository();engine=GovernedSpatialBatchEngine(repo,PassThroughTopologyEngine(),repository_revision='rev')
    p=engine.preview(['NG-PLC-000001']);token=confirmation_token(p.database_name,p.fingerprint)
    engine.execute(['NG-PLC-000001'],approved_fingerprint=p.fingerprint,confirmation=token,submitter_actor_id='s1',approver_actor_id='a1')
    with pytest.raises(SpatialRealizationExecutionError,match='confirmation token'):
        engine.execute(['NG-PLC-000001'],approved_fingerprint=p.fingerprint,confirmation='wrong',submitter_actor_id='s2',approver_actor_id='a2')


def test_blocked_atomic_selection_exposes_candidate_work_but_zero_effective_planned_writes():
    roots=eligible_city_root_ids()[:3]
    repo=MemorySpatialRealizationRepository()
    engine=GovernedSpatialBatchEngine(repo,FailingRootTopology(roots[1]),repository_revision='rev')
    preview=engine.preview(roots)
    assert not preview.execution_ready
    assert preview.candidate_geometry_writes>0
    assert preview.planned_geometry_writes==0
    assert preview.planned_associations==0
