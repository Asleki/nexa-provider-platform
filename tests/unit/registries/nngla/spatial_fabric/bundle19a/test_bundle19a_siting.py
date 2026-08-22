from registries.nngla.spatial_fabric.bundle19a._shared import CRS_CODE, EFFECT_SCOPE
from registries.nngla.spatial_fabric.bundle19a.geometry import containing_polygon, point_relation
from registries.nngla.spatial_fabric.bundle19a.siting import derive_place_reference_points
from registries.nngla.spatial_fabric.bundle19a.source import load_lake_polygons, load_region_anchor_policy, load_sovereign_polygons


def test_all_700_places_receive_unique_governed_reference_points():
    rows = derive_place_reference_points()
    assert len(rows) == 700
    assert len({r.place_id for r in rows}) == 700
    assert len({(r.longitude, r.latitude) for r in rows}) == 700
    assert all(r.crs_code == CRS_CODE and r.runtime_effect_scope == EFFECT_SCOPE for r in rows)
    assert all(r.geometry_reservation_key == f"p006.7.11.10:place-reference:{r.place_id}" for r in rows)


def test_eight_city_anchors_match_governed_anchor_policy():
    by_source = {r.source_place_code: r for r in derive_place_reference_points()}
    anchors = load_region_anchor_policy()
    assert len(anchors) == 8
    for row in anchors:
        point = by_source[row["anchor_source_place_code"]]
        assert point.place_type_code == "CITY"
        assert point.region_code == row["region_code"]
        assert point.supporting_spatial_point_id == row["supporting_spatial_point_id"]
        assert point.longitude == float(row["anchor_longitude"])
        assert point.latitude == float(row["anchor_latitude"])


def test_reference_points_are_sovereign_and_lake_exception_is_explicit():
    sovereign = load_sovereign_polygons()
    lakes = load_lake_polygons()
    in_lake = []
    for row in derive_place_reference_points():
        assert containing_polygon((row.longitude, row.latitude), sovereign) is not None
        for lake in lakes:
            if point_relation((row.longitude, row.latitude), lake["ring"]) in {"INSIDE", "BOUNDARY"}:
                in_lake.append((row.source_place_code, row.exception_code))
    assert in_lake == [("NGP-000345", "INLAND_ISLAND_PHYSICAL_GEOMETRY_PENDING")]


def test_reference_point_derivation_is_process_deterministic_via_stable_candidates():
    first = derive_place_reference_points()
    second = derive_place_reference_points()
    assert first == second
    assert first is second  # cached immutable result; no hidden random regeneration
