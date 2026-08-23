"""Cross-domain road relationships derived without optional geometry dependencies."""
from __future__ import annotations

from ._shared import HYDROLOGY, json_payload, stable_id
from .contracts import RoadAlignment, RoadSpatialRelationship
from .authoring import author_road_alignments
from .geometry import line_intersections_with_linear_geometry, line_intersections_with_polygon


def derive_relationships(alignments: tuple[RoadAlignment, ...] | None = None) -> tuple[RoadSpatialRelationship, ...]:
    roads = alignments or author_road_alignments()
    hydro = json_payload(HYDROLOGY)
    rivers = [(r["riverId"], r["geometry"]) for r in hydro["rivers"]]
    lakes = [(l["lakeId"], l["geometry"]) for l in hydro["lakes"]]
    out: list[RoadSpatialRelationship] = []
    for r in roads:
        out.extend([
            RoadSpatialRelationship(stable_id("roadrel:nngla:", r.road_id, "START", r.start_place_id), r.road_id, "STARTS_AT_PLACE", r.start_place_id, "BUNDLE19A_PLACE_REFERENCE_ENDPOINT", *r.coordinates[0]),
            RoadSpatialRelationship(stable_id("roadrel:nngla:", r.road_id, "END", r.end_place_id), r.road_id, "ENDS_AT_PLACE", r.end_place_id, "BUNDLE19A_PLACE_REFERENCE_ENDPOINT", *r.coordinates[-1]),
            RoadSpatialRelationship(stable_id("roadrel:nngla:", r.road_id, "REGION", r.region_code), r.road_id, "WITHIN_ADMIN_REGION", r.region_code, "BUNDLE19B_REGION_CONTAINMENT"),
        ])
        for river_id, geometry in rivers:
            points = line_intersections_with_linear_geometry(r.coordinates, geometry)
            if points:
                x, y = points[0]
                out.append(RoadSpatialRelationship(
                    stable_id("roadrel:nngla:", r.road_id, "RIVER", river_id), r.road_id, "CROSSES_RIVER", river_id,
                    "GEOMETRIC_INTERSECTION_NOT_BRIDGE_ASSERTION", x, y,
                ))
        for lake_id, geometry in lakes:
            points = line_intersections_with_polygon(r.coordinates, geometry)
            if points:
                x, y = points[0]
                out.append(RoadSpatialRelationship(
                    stable_id("roadrel:nngla:", r.road_id, "LAKE", lake_id), r.road_id, "INTERSECTS_LAKE", lake_id,
                    "GEOMETRIC_INTERSECTION_REQUIRES_LATER_INFRASTRUCTURE_DECISION", x, y,
                ))
    return tuple(sorted(out, key=lambda x: x.relationship_id))
