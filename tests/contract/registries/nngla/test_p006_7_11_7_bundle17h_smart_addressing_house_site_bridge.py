from concurrent.futures import ThreadPoolExecutor
from registries.nngla.spatial_fabric.bundle17h import (
    AddressNumberCollisionError, AddressSeriesDefinition, MemoryAddressAllocator,
    bundle17h_is_qualified, derive_road_segment_candidates, form_site_candidate,
    load_house_site_requirements, load_schema17h_sql, qualify_schema17h_sql,
)
from registries.nngla.spatial_fabric.bundle17h._shared import DAY_ZERO_ADDRESS_PATH, csv_rows
from registries.nngla.spatial_fabric.bundle17h.artifacts import artifact_paths


def test_bundle17h_contract_preserves_locked_roads_and_day_zero_address_provenance_while_extending_with_subordinate_scopes():
    segments = derive_road_segment_candidates()
    assert len(segments) == 350
    assert {s.road_id for s in segments} == {f"NG-RD-{i:06d}" for i in range(1,351)}
    assert csv_rows(DAY_ZERO_ADDRESS_PATH) == ()
    assert csv_rows(artifact_paths()["address_reference_v002"]) == ()


def test_bundle17h_contract_supports_1000_simultaneous_valid_scoped_address_reservations_without_duplicates():
    segment = derive_road_segment_candidates()[0]
    series = AddressSeriesDefinition("addrseries:nngla:contract", segment.road_id, segment.road_segment_id, "SEQUENTIAL", "ROAD_SEGMENT", segment.road_segment_id, 1, 1, "INTEGER", "NONE", False)
    allocator = MemoryAddressAllocator()
    def reserve(i):
        site = form_site_candidate(road_id=segment.road_id, road_segment_id=segment.road_segment_id, source_reference=f"contract:{i}")
        return allocator.reserve_next(series, site_id=site.site_id, idempotency_key=f"contract:{i}")
    with ThreadPoolExecutor(max_workers=48) as pool:
        rows = tuple(pool.map(reserve, range(1000)))
    assert len({r.reserved_address_id for r in rows}) == 1000
    assert len({(r.series_id,r.normalized_number_key) for r in rows}) == 1000


def test_bundle17h_contract_house_bridge_keeps_parcel_site_structure_address_and_residence_separate_and_sql_fail_closed():
    requirements = load_house_site_requirements(artifact_paths()["house_site_requirements"])
    assert len(requirements) == 120
    assert all(req.physical_property_id_issue_stage == "validated_construction_commencement" for req in requirements)
    sql = load_schema17h_sql()
    assert qualify_schema17h_sql(sql) == ()
    assert bundle17h_is_qualified()
