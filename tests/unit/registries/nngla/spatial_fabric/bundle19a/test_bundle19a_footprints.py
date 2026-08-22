from collections import Counter

from registries.nngla.spatial_fabric.bundle19a.contracts import GeometryRole
from registries.nngla.spatial_fabric.bundle19a.footprints import derive_point_only_exceptions, derive_settlement_footprints
from registries.nngla.spatial_fabric.bundle19a.geometry import point_relation, ring_self_intersects
from registries.nngla.spatial_fabric.bundle19a.siting import derive_place_reference_points


def test_footprint_and_point_only_outcomes_cover_all_places_exactly_once():
    footprints = derive_settlement_footprints()
    exceptions = derive_point_only_exceptions()
    points = derive_place_reference_points()
    assert len(footprints) == 419
    assert len(exceptions) == 281
    assert {x.place_id for x in footprints}.isdisjoint({x.place_id for x in exceptions})
    assert {x.place_id for x in footprints} | {x.place_id for x in exceptions} == {x.place_id for x in points}


def test_footprints_never_claim_administrative_or_legal_boundary_semantics():
    for row in derive_settlement_footprints():
        assert row.geometry_role_code is GeometryRole.SETTLEMENT_FOOTPRINT
        assert row.qualification_status == "QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY"
        assert "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY" in row.source_basis
        assert not ring_self_intersects(row.ring)


def test_every_footprint_covers_its_reference_point():
    points = {r.place_id: r for r in derive_place_reference_points()}
    for footprint in derive_settlement_footprints():
        point = points[footprint.place_id]
        assert point_relation((point.longitude, point.latitude), footprint.ring) in {"INSIDE", "BOUNDARY"}


def test_point_only_outcomes_are_explicit_and_heron_is_preserved_as_exception():
    rows = derive_point_only_exceptions()
    counts = Counter(r.reason_code for r in rows)
    assert counts["POINT_ONLY_NO_JUSTIFIED_SETTLEMENT_EXTENT"] == 280
    assert counts["INLAND_ISLAND_PHYSICAL_GEOMETRY_PENDING"] == 1
    heron = next(r for r in rows if r.source_place_code == "NGP-000345")
    assert heron.place_id == "NG-PLC-000345"
