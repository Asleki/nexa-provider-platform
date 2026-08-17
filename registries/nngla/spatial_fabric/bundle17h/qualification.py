"""Bundle 17H qualification: immutable Day-Zero address source, concurrency and house/site separation."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from ._shared import DAY_ZERO_ADDRESS_PATH, HOUSE_CATALOGUE_SHA256, csv_rows
from .address_allocator import AddressNumberCollisionError, MemoryAddressAllocator
from .artifacts import artifact_drift_findings, artifact_paths
from .contracts import AddressSeriesDefinition
from .postgresql_contract import load_schema17h_sql, qualify_schema17h_sql
from .road_segments import derive_road_segment_candidates
from .site_bridge import form_site_candidate, load_house_crosswalk, load_house_site_requirements, site_meets_house_requirement


def bundle17h_findings() -> tuple[str, ...]:
    findings: list[str] = []
    if csv_rows(DAY_ZERO_ADDRESS_PATH):
        findings.append("DAY_ZERO_ADDRESS_REGISTER_MUST_REMAIN_EMPTY")
    segments = derive_road_segment_candidates()
    if len(segments) != 350 or len({row.road_id for row in segments}) != 350:
        findings.append("LOCKED_350_ROAD_SEGMENT_BASELINE_DRIFT")
    findings.extend(artifact_drift_findings())
    findings.extend(qualify_schema17h_sql(load_schema17h_sql()))
    paths = artifact_paths()
    crosswalk = csv_rows(paths["house_crosswalk"])
    requirements = csv_rows(paths["house_site_requirements"])
    if any(row["source_catalogue_sha256"] != HOUSE_CATALOGUE_SHA256 for row in crosswalk + requirements):
        findings.append("HOUSE_CATALOGUE_SOURCE_HASH_DRIFT")
    try:
        loaded_crosswalk = load_house_crosswalk(paths["house_crosswalk"])
        loaded_req = load_house_site_requirements(paths["house_site_requirements"])
        if len(loaded_crosswalk) != 120 or len(loaded_req) != 120:
            findings.append("HOUSE_BRIDGE_CONTRACT_ROW_COUNT_INVALID")
        if not site_meets_house_requirement(
            loaded_req[0], terrain_zone=loaded_req[0].primary_compatible_terrain_zone,
            plot_area_sqm=loaded_req[0].minimum_plot_area_sqm, site_slope_percent=Decimal("0"),
            ground_condition=loaded_req[0].suitable_ground_conditions[0],
        ):
            findings.append("HOUSE_SITE_REQUIREMENT_EVALUATION_FAILED")
    except Exception as exc:
        findings.append(f"HOUSE_BRIDGE_INVALID:{exc}")

    # High-concurrency proof in memory. Bundle 17J later attacks database/runtime recovery in depth.
    try:
        series = AddressSeriesDefinition(
            series_id="addrseries:nngla:qualification", road_id="NG-RD-000001", road_segment_id=segments[0].road_segment_id,
            policy_code="SEQUENTIAL", scope_type="ROAD_SEGMENT", scope_reference=segments[0].road_segment_id,
            start_number=1, sequence_step=1, number_format_rule_code="INTEGER", side_rule="NONE", allow_suffix=False,
        )
        allocator = MemoryAddressAllocator()
        def one(index: int):
            site = form_site_candidate(road_id="NG-RD-000001", road_segment_id=segments[0].road_segment_id, source_reference=f"qualification:site:{index}")
            return allocator.reserve_next(series, site_id=site.site_id, idempotency_key=f"qualification:{index}")
        with ThreadPoolExecutor(max_workers=32) as pool:
            reservations = tuple(pool.map(one, range(1000)))
        if len({row.reserved_address_id for row in reservations}) != 1000 or len({row.normalized_number_key for row in reservations}) != 1000:
            findings.append("CONCURRENT_ADDRESS_ALLOCATION_DUPLICATE")
        # Same visible number is legal in another governed series, illegal in the same series.
        other = AddressSeriesDefinition(
            series_id="addrseries:nngla:qualification-other", road_id="NG-RD-000002", road_segment_id=segments[1].road_segment_id,
            policy_code="SEQUENTIAL", scope_type="ROAD_SEGMENT", scope_reference=segments[1].road_segment_id,
            start_number=1, sequence_step=1, number_format_rule_code="INTEGER", side_rule="NONE", allow_suffix=False,
        )
        other_allocator = MemoryAddressAllocator(start_address_sequence=2001)
        other_allocator.reserve_specific(other, site_id="site:nngla:other", display_number="14", idempotency_key="other:14")
        collision_allocator = MemoryAddressAllocator(start_address_sequence=3001)
        collision_allocator.reserve_specific(series, site_id="site:nngla:a", display_number="14", idempotency_key="a")
        try:
            collision_allocator.reserve_specific(series, site_id="site:nngla:b", display_number="14", idempotency_key="b")
            findings.append("SAME_SCOPE_DUPLICATE_NOT_BLOCKED")
        except AddressNumberCollisionError:
            pass
    except Exception as exc:
        findings.append(f"ADDRESS_CONCURRENCY_PROOF_FAILED:{exc}")
    return tuple(findings)


def bundle17h_is_qualified() -> bool:
    return not bundle17h_findings()


__all__ = ["bundle17h_findings", "bundle17h_is_qualified"]
