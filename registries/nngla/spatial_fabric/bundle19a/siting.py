"""Deterministic hierarchical siting for all 700 canonical NoveGeo places."""
from __future__ import annotations

from functools import lru_cache

from collections import defaultdict

from ._shared import CRS_CODE, EFFECT_SCOPE, deterministic_fraction, stable_id
from .contracts import PlaceReferencePointCandidate, SpatialOutcomeStatus
from .geometry import (
    containing_polygon, haversine_m, offset_coordinate, point_relation, polygons_intersect, regular_ring, ring_is_within
)
from .source import (
    load_island_policy,
    load_lake_polygons,
    load_region_anchor_policy,
    load_settlement_policy,
    load_settlement_requirements,
    load_sovereign_polygons,
    load_support_points,
)

_GOLDEN_ANGLE = 137.50776405003785
_MAX_REGION_DISTANCE_KM = 210.0


def _depth(source_place_code: str, by_source: dict[str, object], trail: frozenset[str] = frozenset()) -> int:
    if source_place_code in trail:
        raise ValueError(f"place hierarchy cycle detected at {source_place_code}")
    row = by_source[source_place_code]
    parent = row.parent_source_place_code
    if not parent:
        return 0
    if parent not in by_source:
        raise ValueError(f"missing parent place {parent} for {source_place_code}")
    return 1 + _depth(parent, by_source, trail | {source_place_code})


def _nearest_support(longitude: float, latitude: float, supports, *, sovereign_part_id: str | None = None):
    pool = supports if sovereign_part_id is None else tuple(item for item in supports if item.sovereign_part_id == sovereign_part_id)
    if not pool:
        raise ValueError(f"no canonical spatial support point for sovereign part {sovereign_part_id}")
    return min(
        pool,
        key=lambda item: (haversine_m(longitude, latitude, item.longitude, item.latitude), item.spatial_point_id),
    )


def _inside_lake(longitude: float, latitude: float, lakes) -> str:
    for lake in lakes:
        if point_relation((longitude, latitude), lake["ring"]) in {"INSIDE", "BOUNDARY"}:
            return str(lake["lake_id"])
    return ""


def _is_separated(longitude: float, latitude: float, existing, minimum_km: float) -> bool:
    threshold = minimum_km * 1000.0
    return all(haversine_m(longitude, latitude, item.longitude, item.latitude) >= threshold for item in existing)


def _candidate_from_parent(requirement, parent, policy, region_anchor, sovereign_polygons, lakes, existing):
    min_km = float(policy["parent_distance_min_km"])
    max_km = float(policy["parent_distance_max_km"])
    minimum_separation = float(policy["minimum_separation_km"])
    if max_km < min_km or min_km <= 0:
        raise ValueError(f"invalid orbit policy for {requirement.place_type_code}")
    base_angle = deterministic_fraction(requirement.source_place_code, requirement.canonical_name, "bearing") * 360.0
    base_fraction = deterministic_fraction(requirement.source_place_code, requirement.region_code, "radius")
    base_radius = min_km + (max_km - min_km) * base_fraction
    mainland = next(item for item in sovereign_polygons if item["sovereign_part_id"] == "NG-SOV-PART-000001")
    for attempt in range(720):
        angle = (base_angle + attempt * _GOLDEN_ANGLE) % 360.0
        radial_cycle = ((attempt // 24) % 9) - 4
        radius = base_radius + radial_cycle * (max_km - min_km) * 0.035
        radius = max(min_km, min(max_km, radius))
        longitude, latitude = offset_coordinate(parent.longitude, parent.latitude, radius, angle)
        if point_relation((longitude, latitude), mainland["ring"]) != "INSIDE":
            continue
        if _inside_lake(longitude, latitude, lakes):
            continue
        minimum_footprint = float(policy["minimum_footprint_radius_km"])
        if minimum_footprint > 0:
            clearance_ring = regular_ring(longitude, latitude, minimum_footprint, vertices=16)
            if not ring_is_within(clearance_ring, mainland["ring"]):
                continue
            if any(polygons_intersect(clearance_ring, lake["ring"]) for lake in lakes):
                continue
        if haversine_m(longitude, latitude, region_anchor.longitude, region_anchor.latitude) > _MAX_REGION_DISTANCE_KM * 1000.0:
            continue
        if not _is_separated(longitude, latitude, existing, minimum_separation):
            continue
        return longitude, latitude, attempt
    raise ValueError(f"unable to deterministically site {requirement.source_place_code} within governed constraints")


@lru_cache(maxsize=1)
def derive_place_reference_points() -> tuple[PlaceReferencePointCandidate, ...]:
    requirements = load_settlement_requirements()
    policies = load_settlement_policy()
    anchor_rows = load_region_anchor_policy()
    island_rows = load_island_policy()
    supports = load_support_points()
    support_by_id = {item.spatial_point_id: item for item in supports}
    sovereign_polygons = load_sovereign_polygons()
    lakes = load_lake_polygons()
    by_source = {item.source_place_code: item for item in requirements}
    canonical_by_source = {item.source_place_code: item.place_id for item in requirements}

    anchors = {}
    for row in anchor_rows:
        requirement = by_source[row["anchor_source_place_code"]]
        support = support_by_id[row["supporting_spatial_point_id"]]
        if requirement.place_type_code != "CITY" or requirement.region_code != row["region_code"]:
            raise ValueError(f"region anchor policy does not align with canonical city {requirement.source_place_code}")
        if abs(support.longitude - float(row["anchor_longitude"])) > 1e-9 or abs(support.latitude - float(row["anchor_latitude"])) > 1e-9:
            raise ValueError(f"region anchor policy coordinate diverges from {support.spatial_point_id}")
        anchors[row["region_code"]] = support

    order = sorted(requirements, key=lambda item: (_depth(item.source_place_code, by_source), int(item.source_place_code.rsplit("-", 1)[1])))
    placements: dict[str, PlaceReferencePointCandidate] = {}
    existing: list[PlaceReferencePointCandidate] = []
    for requirement in order:
        policy = policies[requirement.place_type_code]
        exception_code = ""
        if requirement.place_type_code == "CITY":
            support = anchors[requirement.region_code]
            longitude, latitude = support.longitude, support.latitude
            sovereign_part_id = support.sovereign_part_id
            placement_basis = f"REGION_ANCHOR_POLICY:{requirement.region_code}:{support.spatial_point_id}"
            outcome = SpatialOutcomeStatus.QUALIFIED
            support_distance = 0.0
        elif requirement.place_type_code == "ISLAND_SETTLEMENT":
            island = island_rows.get(requirement.source_place_code)
            if island is None:
                raise ValueError(f"missing island siting policy for {requirement.source_place_code}")
            support = support_by_id[island["supporting_spatial_point_id"]]
            if support.sovereign_part_id != island["sovereign_part_id"]:
                raise ValueError(f"island policy sovereign-part mismatch for {requirement.source_place_code}")
            longitude, latitude = support.longitude, support.latitude
            sovereign_part_id = support.sovereign_part_id
            placement_basis = f"{island['assignment_mode']}:{island['physical_context_reference']}:{support.spatial_point_id}"
            exception_code = island["exception_code"]
            outcome = SpatialOutcomeStatus.QUALIFIED_WITH_EXCEPTION if exception_code else SpatialOutcomeStatus.QUALIFIED
            support_distance = 0.0
        else:
            parent_source = requirement.parent_source_place_code or requirement.major_city_source_place_code
            if not parent_source or parent_source not in placements:
                raise ValueError(f"hierarchical siting parent unavailable for {requirement.source_place_code}")
            parent = placements[parent_source]
            region_anchor_support = anchors[requirement.region_code]
            anchor_reference = PlaceReferencePointCandidate(
                reference_candidate_id="placeref:nngla:anchor-placeholder",
                source_place_code=requirement.major_city_source_place_code,
                place_id=canonical_by_source[requirement.major_city_source_place_code],
                canonical_name=by_source[requirement.major_city_source_place_code].canonical_name,
                place_type_code="CITY",
                region_code=requirement.region_code,
                parent_source_place_code="",
                longitude=region_anchor_support.longitude,
                latitude=region_anchor_support.latitude,
                crs_code=CRS_CODE,
                sovereign_part_id=region_anchor_support.sovereign_part_id,
                supporting_spatial_point_id=region_anchor_support.spatial_point_id,
                support_distance_m=0.0,
                placement_basis="ANCHOR_REFERENCE_ONLY",
                geometry_reservation_key=f"p006.7.11.10:place-reference:{canonical_by_source[requirement.major_city_source_place_code]}",
                outcome_status=SpatialOutcomeStatus.QUALIFIED,
                exception_code="",
                runtime_effect_scope=EFFECT_SCOPE,
            )
            longitude, latitude, attempt = _candidate_from_parent(
                requirement,
                parent,
                policy,
                anchor_reference,
                sovereign_polygons,
                lakes,
                existing,
            )
            containing = containing_polygon((longitude, latitude), sovereign_polygons)
            if containing is None:
                raise ValueError(f"derived point escaped sovereign boundary for {requirement.source_place_code}")
            sovereign_part_id = str(containing["sovereign_part_id"])
            if sovereign_part_id != "NG-SOV-PART-000001":
                raise ValueError(f"ordinary place unexpectedly sited on offshore part for {requirement.source_place_code}")
            support = _nearest_support(longitude, latitude, supports, sovereign_part_id=sovereign_part_id)
            support_distance = haversine_m(longitude, latitude, support.longitude, support.latitude)
            placement_basis = (
                f"DETERMINISTIC_{policy['placement_mode']}:PARENT={parent.place_id}:"
                f"POLICY={requirement.place_type_code}:ATTEMPT={attempt}:SUPPORT={support.spatial_point_id}"
            )
            outcome = SpatialOutcomeStatus.QUALIFIED

        candidate = PlaceReferencePointCandidate(
            reference_candidate_id=stable_id("placeref:nngla:", requirement.place_id, longitude, latitude, placement_basis),
            source_place_code=requirement.source_place_code,
            place_id=requirement.place_id,
            canonical_name=requirement.canonical_name,
            place_type_code=requirement.place_type_code,
            region_code=requirement.region_code,
            parent_source_place_code=requirement.parent_source_place_code,
            longitude=longitude,
            latitude=latitude,
            crs_code=CRS_CODE,
            sovereign_part_id=sovereign_part_id,
            supporting_spatial_point_id=support.spatial_point_id,
            support_distance_m=round(support_distance, 3),
            placement_basis=placement_basis,
            geometry_reservation_key=f"p006.7.11.10:place-reference:{requirement.place_id}",
            outcome_status=outcome,
            exception_code=exception_code,
            runtime_effect_scope=EFFECT_SCOPE,
        )
        placements[requirement.source_place_code] = candidate
        existing.append(candidate)

    result = tuple(sorted(placements.values(), key=lambda item: int(item.source_place_code.rsplit("-", 1)[1])))
    if len(result) != 700:
        raise AssertionError("deterministic place siting did not produce exactly 700 outcomes")
    return result


__all__ = ["derive_place_reference_points"]
