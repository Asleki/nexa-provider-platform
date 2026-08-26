from registries.nngla.spatial_realization.persistence import MemorySpatialRealizationRepository
from registries.nngla.spatial_realization.preview import build_preview,confirmation_token
from registries.nngla.spatial_realization.selection import eligible_city_root_ids
from registries.nngla.spatial_realization.topology import PassThroughTopologyEngine


def test_preview_is_order_independent_and_supports_all_eight_roots():
    roots=eligible_city_root_ids();repo=MemorySpatialRealizationRepository();top=PassThroughTopologyEngine()
    a=build_preview(repo,top,root_ids=roots,repository_revision='rev')
    b=build_preview(repo,top,root_ids=reversed(roots),repository_revision='rev')
    assert a.fingerprint==b.fingerprint
    assert a.execution_ready and len(a.normalized_root_ids)==8
    assert a.planned_geometry_writes==88
    assert a.planned_associations==80


def test_confirmation_token_binds_database_and_preview():
    repo=MemorySpatialRealizationRepository();top=PassThroughTopologyEngine()
    p=build_preview(repo,top,root_ids=['NG-PLC-000001'],repository_revision='rev')
    assert confirmation_token(p.database_name,p.fingerprint)==f'REALIZE-NNGLA-CITIES::{p.database_name}::{p.fingerprint}'


def test_preview_fingerprint_carries_supporting_reference_and_repair_mode_contract():
    repo=MemorySpatialRealizationRepository();top=PassThroughTopologyEngine()
    p=build_preview(repo,top,root_ids=['NG-PLC-000001'],repository_revision='rev')
    assert p.repair_mode=='TEST_PASSTHROUGH'
    assert p.closures[0].supporting_spatial_point_id=='NG-SPT-000629'


def test_effective_date_is_part_of_preview_identity_and_cannot_drift_silently():
    top=PassThroughTopologyEngine()
    a=build_preview(MemorySpatialRealizationRepository(effective_date='2026-08-25'),top,root_ids=['NG-PLC-000001'],repository_revision='rev')
    b=build_preview(MemorySpatialRealizationRepository(effective_date='2026-08-26'),top,root_ids=['NG-PLC-000001'],repository_revision='rev')
    assert a.effective_date=='2026-08-25'
    assert b.effective_date=='2026-08-26'
    assert a.fingerprint!=b.fingerprint


def test_r3_preview_uses_v2_policy_and_includes_canonical_child_seed_evidence_in_identity():
    from registries.nngla.spatial_realization.preview import PLAN_VERSION,_closure_payload
    from registries.nngla.spatial_realization.topology import TOPOLOGY_POLICY_ID,REPAIR_POLICY_ID
    repo=MemorySpatialRealizationRepository();top=PassThroughTopologyEngine()
    p=build_preview(repo,top,root_ids=['NG-PLC-000001'],repository_revision='rev')
    assert PLAN_VERSION==2 and p.plan_version==2
    assert TOPOLOGY_POLICY_ID.endswith('-v2') and REPAIR_POLICY_ID.endswith('-v2')
    payload=_closure_payload(p.closures[0])
    assert len(payload['exhaustive_child_seeds'])==8
