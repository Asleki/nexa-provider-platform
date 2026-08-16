from collections import Counter

from registries.nngla.spatial_fabric.bundle17b.source_fidelity import (
    derive_source_fidelity_results,
    source_fidelity_findings,
)


def test_all_5322_coordinate_occurrences_retain_immutable_source_file_and_lineage_fidelity():
    rows = derive_source_fidelity_results()
    assert len(rows) == 5322
    assert source_fidelity_findings(rows) == ()
    assert all(row.expected_source_sha256 == row.actual_source_sha256 for row in rows)
    assert all(row.dataset_lineage_match != "MISMATCH" for row in rows)
    assert all(row.crs_lineage_match == "MATCHED" for row in rows)


def test_core_terrain_climate_and_vegetation_rows_match_qualified_parent_attributes_not_only_csv_hashes():
    rows = derive_source_fidelity_results()
    matched = Counter(row.source_file_id for row in rows if row.source_attribute_match == "MATCHED")
    assert matched == Counter({
        "NG-SPFILE-001": 276,
        "NG-SPFILE-002": 1104,
        "NG-SPFILE-007": 1104,
        "NG-SPFILE-008": 276,
    })


def test_boundary_coordinates_are_reconciled_to_source_geometry_and_sea_route_intermediates_remain_declared_derivatives():
    rows = derive_source_fidelity_results()
    boundary = [row for row in rows if row.source_file_id == "NG-SPFILE-010"]
    sea_routes = [row for row in rows if row.source_file_id == "NG-SPFILE-047"]
    assert len(boundary) == 1054
    assert all(row.source_coordinate_match == "MATCHED" for row in boundary)
    assert len(sea_routes) == 25
    assert all(row.source_coordinate_match == "DECLARED_DERIVATION_NOT_RECOMPUTED_17B" for row in sea_routes)
