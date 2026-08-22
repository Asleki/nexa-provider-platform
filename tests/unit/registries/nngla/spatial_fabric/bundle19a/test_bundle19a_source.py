from collections import Counter

from registries.nngla.spatial_fabric.bundle19a._shared import EXPECTED_PLACE_TYPE_COUNTS, EXPECTED_REGION_COUNTS
from registries.nngla.spatial_fabric.bundle19a.source import (
    load_settlement_requirements, load_support_points, qualify_locked_place_baseline,
)


def test_locked_place_baseline_is_exactly_700_and_unchanged():
    rows = load_settlement_requirements()
    assert len(rows) == 700
    assert qualify_locked_place_baseline(rows) is None
    assert [r.source_place_code for r in rows] == [f"NGP-{i:06d}" for i in range(1, 701)]
    assert [r.place_id for r in rows] == [f"NG-PLC-{i:06d}" for i in range(1, 701)]
    assert Counter(r.place_type_code for r in rows) == Counter(EXPECTED_PLACE_TYPE_COUNTS)
    assert Counter(r.region_code for r in rows) == Counter(EXPECTED_REGION_COUNTS)


def test_only_qualified_interior_canonical_spatial_points_are_siting_support():
    rows = load_support_points()
    assert len(rows) == 1348
    assert len({r.spatial_point_id for r in rows}) == 1348
    assert all(r.sovereign_land_relation == "INSIDE_SOVEREIGN_LAND" for r in rows)
