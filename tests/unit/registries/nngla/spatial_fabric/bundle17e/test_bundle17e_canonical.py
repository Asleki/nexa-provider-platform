from collections import Counter

from registries.nngla.spatial_fabric.bundle17e import (
    derive_spatial_canonical_crosswalk,
    existing_spatial_point_mapping,
    migration_action_rows,
)


def test_spatial_crosswalk_preserves_1104_existing_ng_spt_ids_and_allocates_only_missing_positions():
    rows = derive_spatial_canonical_crosswalk()
    existing = existing_spatial_point_mapping()
    assert len(rows) == 2411
    assert len(existing) == 1104
    by_candidate = {row.coordinate_candidate_id: row for row in rows}
    assert all(by_candidate[candidate].canonical_spatial_point_id == point_id for candidate, point_id in existing.items())
    origins = Counter(row.identity_origin for row in rows)
    assert origins == Counter({"NEW_BUNDLE17E_ALLOCATION": 1307, "EXISTING_GOVERNED_SOURCE_IDENTITY": 1104})


def test_initial_canonical_point_range_is_unique_contiguous_and_does_not_rederive_topology():
    rows = derive_spatial_canonical_crosswalk()
    ids = {row.canonical_spatial_point_id for row in rows}
    assert ids == {f"NG-SPT-{number:06d}" for number in range(1, 2412)}
    assert all("TOPOLOGY" not in row.crosswalk_basis for row in rows)


def test_offline_migration_action_contract_requires_live_target_confirmation_and_no_destructive_update():
    rows = migration_action_rows()
    assert len(rows) == 2411
    assert {row["planned_action"] for row in rows} == {"INSERT_NEW"}
    assert {row["requires_live_target_confirmation"] for row in rows} == {"true"}
    assert {row["existing_canonical_rows_destructively_updated"] for row in rows} == {"false"}
