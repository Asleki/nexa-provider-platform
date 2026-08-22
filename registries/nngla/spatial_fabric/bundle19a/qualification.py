"""Milestone qualification for P006.7.11.10."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

from ._shared import EXPECTED_PLACE_TYPE_COUNTS, EXPECTED_REGION_COUNTS
from .contracts import SpatialOutcomeStatus
from .footprints import derive_point_only_exceptions, derive_settlement_footprints
from .geometry import containing_polygon, point_relation, polygons_intersect, ring_is_within, ring_self_intersects
from .relationships import derive_place_spatial_relationships
from .siting import derive_place_reference_points
from .source import (
    load_island_policy,
    load_lake_polygons,
    load_settlement_requirements,
    load_sovereign_polygons,
    load_support_points,
)


@lru_cache(maxsize=1)
def qualification_findings() -> tuple[str, ...]:
    findings: list[str] = []
    requirements = load_settlement_requirements()
    points = derive_place_reference_points()
    footprints = derive_settlement_footprints()
    exceptions = derive_point_only_exceptions()
    relationships = derive_place_spatial_relationships()
    supports = {row.spatial_point_id: row for row in load_support_points()}
    sovereign = {row["sovereign_part_id"]: row for row in load_sovereign_polygons()}
    lakes = load_lake_polygons()
    island_policy = load_island_policy()

    if len(points) != 700:
        findings.append(f"place-reference-count:{len(points)}")
    if len({row.place_id for row in points}) != 700 or len({(row.longitude, row.latitude) for row in points}) != 700:
        findings.append("place-reference-identity-or-coordinate-collision")
    if Counter(row.place_type_code for row in points) != Counter(EXPECTED_PLACE_TYPE_COUNTS):
        findings.append("place-type-distribution-changed")
    if Counter(row.region_code for row in points) != Counter(EXPECTED_REGION_COUNTS):
        findings.append("region-distribution-changed")
    if tuple(row.place_id for row in points) != tuple(row.place_id for row in requirements):
        findings.append("canonical-place-identity-order-changed")

    for point in points:
        polygon = containing_polygon((point.longitude, point.latitude), tuple(sovereign.values()))
        if polygon is None:
            findings.append(f"outside-sovereign:{point.place_id}")
            continue
        if polygon["sovereign_part_id"] != point.sovereign_part_id:
            findings.append(f"sovereign-part-mismatch:{point.place_id}")
        if point.supporting_spatial_point_id not in supports:
            findings.append(f"unknown-support-point:{point.place_id}")
        if point.place_type_code != "ISLAND_SETTLEMENT" and point.sovereign_part_id != "NG-SOV-PART-000001":
            findings.append(f"ordinary-place-offshore:{point.place_id}")
        lake = next((lake for lake in lakes if point_relation((point.longitude, point.latitude), lake["ring"]) in {"INSIDE", "BOUNDARY"}), None)
        if lake:
            policy = island_policy.get(point.source_place_code)
            allowed = bool(
                point.place_type_code == "ISLAND_SETTLEMENT"
                and policy
                and policy["assignment_mode"] == "INLAND_LAKE_REFERENCE"
                and policy["physical_context_reference"] == lake["lake_id"]
                and point.outcome_status is SpatialOutcomeStatus.QUALIFIED_WITH_EXCEPTION
            )
            if not allowed:
                findings.append(f"unqualified-place-in-lake:{point.place_id}")

    footprint_by_place = {row.place_id: row for row in footprints}
    exception_by_place = {row.place_id: row for row in exceptions}
    if len(footprints) != 419:
        findings.append(f"footprint-count:{len(footprints)}")
    if len(exceptions) != 281:
        findings.append(f"point-only-count:{len(exceptions)}")
    if set(footprint_by_place) & set(exception_by_place):
        findings.append("place-both-footprint-and-point-only")
    if set(footprint_by_place) | set(exception_by_place) != {row.place_id for row in points}:
        findings.append("footprint-point-only-coverage-gap")
    if sum(1 for row in exceptions if row.reason_code == "INLAND_ISLAND_PHYSICAL_GEOMETRY_PENDING") != 1:
        findings.append("inland-island-exception-count")

    for footprint in footprints:
        polygon = sovereign[footprint.sovereign_part_id]
        if ring_self_intersects(footprint.ring):
            findings.append(f"self-intersecting-footprint:{footprint.place_id}")
        if not ring_is_within(footprint.ring, polygon["ring"]):
            findings.append(f"footprint-outside-sovereign:{footprint.place_id}")
        point = next(row for row in points if row.place_id == footprint.place_id)
        if point_relation((point.longitude, point.latitude), footprint.ring) not in {"INSIDE", "BOUNDARY"}:
            findings.append(f"reference-point-not-covered:{footprint.place_id}")
        if footprint.sovereign_part_id == "NG-SOV-PART-000001" and any(polygons_intersect(footprint.ring, lake["ring"]) for lake in lakes):
            findings.append(f"footprint-intersects-lake:{footprint.place_id}")
        if "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY" not in footprint.source_basis:
            findings.append(f"legal-boundary-semantics-not-explicit:{footprint.place_id}")

    if len(relationships) != 668:
        findings.append(f"parent-spatial-evidence-count:{len(relationships)}")
    if any(row.qualification_status != "PASS" for row in relationships):
        findings.append("unqualified-parent-spatial-evidence")

    return tuple(findings)


def bundle19a_is_qualified() -> bool:
    return qualification_findings() == ()


__all__ = ["qualification_findings", "bundle19a_is_qualified"]
