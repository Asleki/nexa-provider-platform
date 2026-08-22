from collections import Counter

from registries.nngla.spatial_fabric.bundle19a._shared import EXPECTED_PLACE_TYPE_COUNTS
from registries.nngla.spatial_fabric.bundle19a.footprints import derive_point_only_exceptions, derive_settlement_footprints
from registries.nngla.spatial_fabric.bundle19a.postgresql_contract import bundle19a_requires_schema_migration
from registries.nngla.spatial_fabric.bundle19a.qualification import qualification_findings
from registries.nngla.spatial_fabric.bundle19a.siting import derive_place_reference_points


def test_p006_7_11_10_contract_locks_place_identity_geometry_and_legal_boundaries():
    points = derive_place_reference_points()
    footprints = derive_settlement_footprints()
    exceptions = derive_point_only_exceptions()
    assert qualification_findings() == ()
    assert len(points) == 700
    assert Counter(x.place_type_code for x in points) == Counter(EXPECTED_PLACE_TYPE_COUNTS)
    assert [x.place_id for x in points] == [f"NG-PLC-{i:06d}" for i in range(1, 701)]
    assert len(footprints) == 419 and len(exceptions) == 281
    assert all("NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY" in x.source_basis for x in footprints)
    assert bundle19a_requires_schema_migration() is False
