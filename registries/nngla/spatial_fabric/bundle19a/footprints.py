"""Settlement-footprint derivation with explicit non-legal geometry semantics."""
from __future__ import annotations

from functools import lru_cache

from ._shared import CRS_CODE, EFFECT_SCOPE, stable_id
from .contracts import GeometryRole, PointOnlyException, SettlementFootprintCandidate
from .geometry import polygon_area_sq_km, polygons_intersect, regular_ring, ring_is_within, ring_self_intersects
from .siting import derive_place_reference_points
from .source import load_island_policy, load_lake_polygons, load_settlement_policy, load_sovereign_polygons


def _point_only_reason(point, policy, island_policy):
    if point.place_type_code in {"VILLAGE", "MARKET_CENTRE"}:
        return PointOnlyException(
            source_place_code=point.source_place_code,
            place_id=point.place_id,
            reason_code=policy["reference_point_policy"],
            reason_detail=(
                "The source establishes a canonical settlement identity and governed siting requirement but does not provide "
                "surveyed or otherwise justified settlement extent. Bundle 19A therefore preserves a qualified reference point "
                "without fabricating an areal boundary."
            ),
        )
    island = island_policy.get(point.source_place_code)
    if island and island["footprint_policy"] == "POINT_ONLY":
        return PointOnlyException(
            source_place_code=point.source_place_code,
            place_id=point.place_id,
            reason_code=island["exception_code"],
            reason_detail=island["exception_detail"],
        )
    return None


@lru_cache(maxsize=1)
def derive_settlement_footprints() -> tuple[SettlementFootprintCandidate, ...]:
    points = derive_place_reference_points()
    policies = load_settlement_policy()
    island_policy = load_island_policy()
    sovereign = {item["sovereign_part_id"]: item for item in load_sovereign_polygons()}
    lakes = load_lake_polygons()
    results: list[SettlementFootprintCandidate] = []
    for point in points:
        policy = policies[point.place_type_code]
        exception = _point_only_reason(point, policy, island_policy)
        if exception is not None:
            continue
        nominal = float(policy["footprint_radius_km"])
        minimum = float(policy["minimum_footprint_radius_km"])
        if nominal <= 0 or minimum <= 0:
            raise ValueError(f"footprint-required place has non-positive footprint policy: {point.source_place_code}")
        sovereign_part = sovereign[point.sovereign_part_id]
        realized = nominal
        ring = None
        for _ in range(48):
            candidate = regular_ring(point.longitude, point.latitude, realized, vertices=24)
            sovereign_ok = ring_is_within(candidate, sovereign_part["ring"])
            lake_ok = True
            if point.sovereign_part_id == "NG-SOV-PART-000001":
                lake_ok = not any(polygons_intersect(candidate, lake["ring"]) for lake in lakes)
            if sovereign_ok and lake_ok and not ring_self_intersects(candidate):
                ring = candidate
                break
            realized *= 0.90
            if realized < minimum:
                break
        if ring is None or realized < minimum:
            raise ValueError(
                f"required settlement footprint for {point.source_place_code} cannot be qualified inside sovereign context "
                f"without falling below minimum policy radius {minimum} km"
            )
        results.append(SettlementFootprintCandidate(
            footprint_candidate_id=stable_id(
                "placefootprint:nngla:", point.place_id, point.longitude, point.latitude, round(realized, 6), "SETTLEMENT_FOOTPRINT_V1"
            ),
            source_place_code=point.source_place_code,
            place_id=point.place_id,
            canonical_name=point.canonical_name,
            place_type_code=point.place_type_code,
            region_code=point.region_code,
            geometry_role_code=GeometryRole.SETTLEMENT_FOOTPRINT,
            geometry_type_code="POLYGON",
            ring=ring,
            nominal_radius_km=nominal,
            realized_radius_km=round(realized, 6),
            area_sq_km=round(polygon_area_sq_km(ring), 6),
            crs_code=CRS_CODE,
            sovereign_part_id=point.sovereign_part_id,
            geometry_reservation_key=f"p006.7.11.10:settlement-footprint:{point.place_id}",
            qualification_status="QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY",
            source_basis=(
                "DETERMINISTIC_UNSURVEYED_SETTLEMENT_EXTENT_V1;"
                "PHYSICAL_SETTLEMENT_GEOGRAPHY_ONLY;NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY"
            ),
            runtime_effect_scope=EFFECT_SCOPE,
        ))
    return tuple(results)


@lru_cache(maxsize=1)
def derive_point_only_exceptions() -> tuple[PointOnlyException, ...]:
    policies = load_settlement_policy()
    island_policy = load_island_policy()
    results = []
    for point in derive_place_reference_points():
        exception = _point_only_reason(point, policies[point.place_type_code], island_policy)
        if exception is not None:
            results.append(exception)
    return tuple(results)


__all__ = ["derive_settlement_footprints", "derive_point_only_exceptions"]
