"""Bundle 20A invariant checks using the repository's dependency-free geometry baseline."""
from __future__ import annotations
from collections import Counter

from ._shared import EXPECTED_CLASS_COUNTS, EXPECTED_ROAD_COUNT
from .authoring import author_road_alignments
from .geometry import segment_covered_by_polygonal_geometry
from .source import region_features
from .topology import build_network


def qualify_bundle() -> tuple[str, ...]:
    roads = author_road_alignments()
    findings: list[str] = []
    if len(roads) != EXPECTED_ROAD_COUNT:
        findings.append("ROAD_COUNT")
    if Counter(r.road_class_code for r in roads) != Counter(EXPECTED_CLASS_COUNTS):
        findings.append("ROAD_CLASS_COUNTS")
    if len({r.road_id for r in roads}) != len(roads):
        findings.append("DUPLICATE_ROAD_ID")
    if len({r.coordinates for r in roads}) != len(roads):
        findings.append("DUPLICATE_ALIGNMENT")
    regions = {f["properties"]["region_code"]: f["geometry"] for f in region_features()}
    for r in roads:
        if len(r.coordinates) < 2 or r.coordinates[0] == r.coordinates[-1]:
            findings.append(f"INVALID_GEOMETRY:{r.road_id}")
        if not segment_covered_by_polygonal_geometry(r.coordinates[0], r.coordinates[-1], regions[r.region_code]):
            findings.append(f"REGION_ESCAPE:{r.road_id}")
    nodes, segs, conns = build_network(roads)
    if len(segs) != EXPECTED_ROAD_COUNT or len(conns) != EXPECTED_ROAD_COUNT * 2:
        findings.append("NETWORK_CARDINALITY")
    if not any(n.node_role == "JUNCTION" for n in nodes):
        findings.append("NO_JUNCTIONS")
    return tuple(findings)
