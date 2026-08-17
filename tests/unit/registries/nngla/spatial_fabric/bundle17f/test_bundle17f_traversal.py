import pytest
from registries.nngla.spatial_fabric.bundle17f import (
    construct_free_form_geometry,
    derive_geometry_traversal_qualifications,
    has_arbitrary_direction_segment,
    segment_vectors,
)


def test_existing_21_geometries_are_source_fidelity_qualified_for_free_form_traversal():
    rows = derive_geometry_traversal_qualifications()
    assert len(rows) == 21
    assert all(x.traversal_status == "PASS" for x in rows)
    assert all(x.identifier_sequence_used is False for x in rows)
    assert {x.geometry_type_code for x in rows} == {"POINT", "LINESTRING", "POLYGON", "MULTIPOLYGON"}


def test_free_form_linestring_allows_diagonal_arbitrary_traversal_not_grid_hops():
    geometry = construct_free_form_geometry("LINESTRING", [(30.1, -18.2), (30.73, -17.61), (31.04, -17.88)])
    assert has_arbitrary_direction_segment(geometry)
    assert segment_vectors(geometry)[0] == pytest.approx((0.63, 0.59))


def test_free_form_polygon_is_closed_and_not_constrained_to_cardinal_directions():
    geometry = construct_free_form_geometry("POLYGON", [[(30, -18), (30.7, -17.8), (31.1, -18.4), (30, -18)]])
    assert has_arbitrary_direction_segment(geometry)
    with pytest.raises(ValueError):
        construct_free_form_geometry("POLYGON", [[(30, -18), (31, -18), (31, -17)]])


def test_coordinate_bounds_fail_closed():
    with pytest.raises(ValueError):
        construct_free_form_geometry("POINT", (181, 0))
