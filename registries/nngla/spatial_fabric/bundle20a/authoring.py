"""Deterministic NNGLA simulation road authoring from locked place/admin evidence.

The validated endpoint selection is frozen as a controlled Bundle 20 plan. Runtime
and tests reconstruct the governed LINESTRING from canonical place coordinates
without depending on optional third-party geometry libraries.
"""
from __future__ import annotations
from collections import defaultdict

from ._shared import ROAD_ALIGNMENT_PLAN, csv_rows, haversine_m
from .contracts import RoadAlignment
from .geometry import segment_covered_by_polygonal_geometry
from .source import canonical_road_rows, place_rows, region_features


def author_road_alignments() -> tuple[RoadAlignment, ...]:
    roads = {r["road_id"]: r for r in canonical_road_rows()}
    places = {p["place_id"]: p for p in place_rows()}
    regions = {f["properties"]["region_code"]: f["geometry"] for f in region_features()}
    plan = csv_rows(ROAD_ALIGNMENT_PLAN)

    if len(plan) != len(roads) or {r["road_id"] for r in plan} != set(roads):
        raise ValueError("road alignment plan must cover the exact locked 350 canonical roads")
    if len({(r["start_place_id"], r["end_place_id"]) for r in plan}) != len(plan):
        raise ValueError("road alignment plan contains duplicate endpoint pairs")

    result: list[RoadAlignment] = []
    for item in sorted(plan, key=lambda r: int(r["road_id"].rsplit("-", 1)[1])):
        road = roads[item["road_id"]]
        if item["road_candidate_id"] != road["road_candidate_id"] or item["region_code"] != road["region_code"]:
            raise ValueError(f"road alignment plan/source mismatch: {item['road_id']}")
        if item["authoring_method"] != "FROZEN_VALIDATED_PLANAR_ENDPOINT_SELECTION_V1" or item["plan_status"] != "QUALIFIED_SIMULATION_AUTHORING_PLAN":
            raise ValueError(f"road alignment plan governance mismatch: {item['road_id']}")
        start = places[item["start_place_id"]]
        end = places[item["end_place_id"]]
        region_code = road["region_code"]
        if start["region_code"] != region_code or end["region_code"] != region_code:
            raise ValueError(f"road endpoint region mismatch: {item['road_id']}")
        coords = (
            (float(start["longitude"]), float(start["latitude"])),
            (float(end["longitude"]), float(end["latitude"])),
        )
        if not segment_covered_by_polygonal_geometry(coords[0], coords[1], regions[region_code]):
            raise ValueError(f"frozen road alignment escapes governed region: {item['road_id']}")
        result.append(RoadAlignment(
            road_id=road["road_id"], road_candidate_id=road["road_candidate_id"], road_name_id=road["road_name_id"],
            canonical_name=road["canonical_name"], road_class_code=road["road_class_code"], region_code=region_code,
            start_place_id=start["place_id"], end_place_id=end["place_id"], coordinates=coords,
            length_m=haversine_m(coords), geometry_reservation_key=f"p006.7.11.12:road-alignment:{road['road_id']}",
        ))
    return tuple(result)
