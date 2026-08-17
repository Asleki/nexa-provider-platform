from collections import Counter

from registries.nngla.spatial_fabric.bundle17e import bundle17e_is_qualified, derive_persistence_qualifications


def test_persistence_qualification_covers_every_coordinate_candidate_and_is_green():
    rows = derive_persistence_qualifications()
    assert len(rows) == 2411
    assert Counter(row.qualification_status for row in rows) == Counter({"PASS": 2411})
    assert all(row.source_verified and row.coordinate_valid and row.map_reconciled for row in rows)
    assert all(row.crs_valid and row.precision_valid and row.containment_valid for row in rows)
    assert all(row.canonical_id_stable and row.geometry_assignment_valid and row.crosswalk_valid for row in rows)


def test_environment_and_topology_use_explicit_not_applicable_semantics_instead_of_fabricating_evidence():
    rows = derive_persistence_qualifications()
    environment = Counter(row.environment_applicability for row in rows)
    topology = Counter(row.topology_applicability for row in rows)
    assert environment == Counter({
        "NOT_APPLICABLE_NO_ENVIRONMENT_BINDING_REQUIRED": 1307,
        "APPLICABLE_REFERENCE_FABRIC_POINT": 1104,
    })
    assert topology == Counter({
        "NOT_APPLICABLE_FREE_COORDINATE_NOT_A_REFERENCE_CELL": 1307,
        "APPLICABLE_REFERENCE_CELL_AND_MAJOR_GRID": 1104,
    })
    assert all(row.environment_resolved and row.topology_valid for row in rows)


def test_conflict_qualification_preserves_17c_deferred_full_extent_boundary():
    rows = derive_persistence_qualifications()
    applicability = Counter(row.conflict_applicability for row in rows)
    assert applicability == Counter({
        "NOT_APPLICABLE_NO_ASSERTED_OCCUPANCY_RELATION": 2377,
        "APPLICABLE_REFERENCE_POINT_RELATION_FULL_EXTENT_DEFERRED": 34,
    })
    assert all(row.conflict_free for row in rows)


def test_bundle17e_qualification_requires_bundle17d_and_all_2411_persistence_rows():
    assert bundle17e_is_qualified() is True
