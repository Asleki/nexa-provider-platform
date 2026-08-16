from collections import Counter
from decimal import Decimal

from registries.nngla.spatial_fabric import candidate_identity
from registries.nngla.spatial_fabric.bundle17b._shared import SOURCE_ROOT, csv_rows
from registries.nngla.spatial_fabric.bundle17b.containment import (
    containment_findings,
    derive_containment_qualifications,
)


def test_all_2411_coordinate_candidates_are_qualified_against_actual_boundary_v002_geometry():
    rows = derive_containment_qualifications()
    assert len(rows) == 2411
    assert containment_findings(rows) == ()
    assert Counter(row.sovereign_land_relation.value for row in rows) == Counter({
        "INSIDE_SOVEREIGN_LAND": 1348,
        "ON_SOVEREIGN_BOUNDARY": 1048,
        "OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE": 15,
    })


def test_expected_marine_route_points_are_not_misclassified_as_invalid_land_coordinates():
    rows = derive_containment_qualifications()
    marine = [row for row in rows if row.sovereign_land_relation.value == "OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE"]
    assert len(marine) == 15
    assert all(row.expected_spatial_context == "MARINE_SOURCE_EXPECTED" for row in marine)
    assert all(row.map_extent_status == "WITHIN_GOVERNED_EXTENT" for row in marine)


def test_all_1104_environment_reference_point_centres_are_on_or_inside_sovereign_land():
    rows = {row.coordinate_candidate_id: row for row in derive_containment_qualifications()}
    points = csv_rows(SOURCE_ROOT / "01_spatial_fabric" / "novegeo_spatial_grid_points_v001.csv")
    assert len(points) == 1104
    for point in points:
        candidate_id = candidate_identity(Decimal(point["longitude"]), Decimal(point["latitude"]))
        assert rows[candidate_id].sovereign_land_relation.value in {"INSIDE_SOVEREIGN_LAND", "ON_SOVEREIGN_BOUNDARY"}
