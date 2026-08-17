from registries.nngla.spatial_fabric.bundle17e import (
    derive_effective_dated_assignments,
    derive_geometry_assignments,
    existing_geometry_ids,
)


def test_bundle17e_preserves_existing_21_geometry_ids_and_allocates_after_them():
    existing = existing_geometry_ids()
    rows = derive_geometry_assignments()
    assert len(existing) == 21
    assert set(existing) == {f"NG-GEO-{number:06d}" for number in range(1, 22)}
    assert len(rows) == 2411
    assert rows[0].geometry_id == "NG-GEO-000022"
    assert rows[-1].geometry_id == "NG-GEO-002432"
    assert not (set(existing) & {row.geometry_id for row in rows})


def test_every_canonical_spatial_point_gets_one_point_geometry_without_superseding_history():
    rows = derive_geometry_assignments()
    assert len({row.canonical_spatial_point_id for row in rows}) == 2411
    assert len({row.geometry_id for row in rows}) == 2411
    assert {row.geometry_type_code for row in rows} == {"POINT"}
    assert {row.geometry_role_code for row in rows} == {"SPATIAL_REFERENCE_POINT"}
    assert {row.crs_code for row in rows} == {"NG-CRS-EPSG4326"}
    assert {row.supersedes_geometry_id for row in rows} == {""}


def test_effective_dated_assignment_keeps_subject_identity_separate_from_geometry_identity():
    assignments = derive_effective_dated_assignments()
    assert len(assignments) == 2411
    assert all(row.subject_id != row.geometry_id for row in assignments)
    assert {row.assignment_version for row in assignments} == {1}
    assert {row.assignment_status for row in assignments} == {"QUALIFIED_FOR_PERSISTENCE"}
    assert {row.effective_to for row in assignments} == {""}
