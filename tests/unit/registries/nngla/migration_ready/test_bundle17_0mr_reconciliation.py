from registries.nngla.migration_ready.contracts import ReconciliationAction
from registries.nngla.migration_ready.reconciliation import reconcile_spatial_target
from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate
from registries.nngla.spatial_fabric.bundle17e.geometry import geometry_by_candidate
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


def test_empty_target_classifies_all_2411_as_insert_new():
    repo = MemorySpatialRepository()
    rows = reconcile_spatial_target(repo.snapshot(), canonical_by_candidate(), geometry_by_candidate())
    assert len(rows) == 2411
    assert {row.action for row in rows} == {ReconciliationAction.INSERT_NEW}


def test_exact_persisted_state_is_reused():
    repo = MemorySpatialRepository()
    candidate_id = next(iter(canonical_by_candidate()))
    repo.persist_point(canonical_by_candidate()[candidate_id], geometry_by_candidate()[candidate_id])
    rows = reconcile_spatial_target(repo.snapshot(), canonical_by_candidate(), geometry_by_candidate())
    by_id = {row.coordinate_candidate_id: row for row in rows}
    assert by_id[candidate_id].action is ReconciliationAction.REUSE_CANONICAL


def test_orphaned_canonical_identifier_fails_closed():
    repo = MemorySpatialRepository()
    candidate_id, crosswalk = next(iter(canonical_by_candidate().items()))
    repo.spatial_points[crosswalk.canonical_spatial_point_id] = {"record_family": "SPATIAL_REFERENCE_POINT"}
    rows = reconcile_spatial_target(repo.snapshot(), canonical_by_candidate(), geometry_by_candidate())
    by_id = {row.coordinate_candidate_id: row for row in rows}
    assert by_id[candidate_id].action is ReconciliationAction.CONFLICT
    assert by_id[candidate_id].reason == "CANONICAL_ID_OCCUPIED_WITHOUT_EXPECTED_CROSSWALK"
