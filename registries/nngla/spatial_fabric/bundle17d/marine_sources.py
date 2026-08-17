"""Read and cross-check the immutable eleven-file New Waters v001 source family."""
from __future__ import annotations

from functools import lru_cache

from ._shared import MARINE_ROOT, csv_rows, source_reference_matches

MARINE_FILES = (
    "novegeo_marine_waterbodies_v001.csv",
    "novegeo_marine_waterbody_vertices_v001.csv",
    "novegeo_marine_coastal_interfaces_v001.csv",
    "novegeo_marine_route_anchor_points_v001.csv",
    "novegeo_sea_route_candidates_v001.csv",
    "novegeo_sea_route_vertices_v001.csv",
    "novegeo_sea_route_derivation_crosswalk_v001.csv",
    "novegeo_island_mainland_connections_v001.csv",
    "novegeo_marine_route_validation_v001.csv",
    "novegeo_island_physical_state_v001.csv",
    "novegeo_sea_route_name_catalogue_v001.csv",
)


@lru_cache(maxsize=1)
def load_marine_sources() -> dict[str, tuple[dict[str, str], ...]]:
    return {name: csv_rows(MARINE_ROOT / name) for name in MARINE_FILES}


def marine_source_findings() -> tuple[str, ...]:
    data = load_marine_sources()
    findings: list[str] = []
    if set(data) != set(MARINE_FILES):
        findings.append("MARINE_SOURCE_INVENTORY_INCOMPLETE")
    expected_counts = {
        "novegeo_marine_waterbodies_v001.csv": 1,
        "novegeo_marine_waterbody_vertices_v001.csv": 0,
        "novegeo_marine_coastal_interfaces_v001.csv": 23,
        "novegeo_marine_route_anchor_points_v001.csv": 10,
        "novegeo_sea_route_candidates_v001.csv": 5,
        "novegeo_sea_route_vertices_v001.csv": 25,
        "novegeo_sea_route_derivation_crosswalk_v001.csv": 25,
        "novegeo_island_mainland_connections_v001.csv": 5,
        "novegeo_marine_route_validation_v001.csv": 5,
        "novegeo_island_physical_state_v001.csv": 5,
        "novegeo_sea_route_name_catalogue_v001.csv": 180,
    }
    for name, count in expected_counts.items():
        if len(data[name]) != count:
            findings.append(f"UNEXPECTED_SOURCE_COUNT:{name}:{len(data[name])}!={count}")
    for name, rows in data.items():
        for index, row in enumerate(rows, start=2):
            if not source_reference_matches(row):
                findings.append(f"SOURCE_REFERENCE_DRIFT:{name}:{index}")
    return tuple(findings)


__all__ = ["MARINE_FILES", "load_marine_sources", "marine_source_findings"]
