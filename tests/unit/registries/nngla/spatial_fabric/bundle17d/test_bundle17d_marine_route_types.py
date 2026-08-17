from registries.nngla.spatial_fabric.bundle17d import marine_route_types


def test_bundle17d_route_type_keeps_physical_route_independent_of_name():
    rows = marine_route_types()
    assert len(rows) == 1
    route = rows[0]
    assert route.marine_route_type_code == "MAINLAND_TO_OFFSHORE_ISLAND"
    assert route.geometry_type_code == "LINESTRING"
    assert route.start_anchor_role == "MAINLAND_DEPARTURE"
    assert route.end_anchor_role == "ISLAND_ARRIVAL"
    assert not route.may_cross_land
    assert not route.physical_qualification_requires_name
