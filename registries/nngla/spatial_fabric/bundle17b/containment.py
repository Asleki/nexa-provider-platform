"""Bundle 17B sovereign containment against the actual six-part boundary geometry."""
from __future__ import annotations

from functools import lru_cache
from collections import defaultdict
from decimal import Decimal

from registries.nngla.spatial_fabric import derive_coordinate_candidates, derive_coordinate_occurrences, load_manifest

from ._shared import SOURCE_ROOT, csv_rows
from .contracts import ContainmentQualification, SovereignLandRelation

_BOUNDARY_VERTICES = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_world_boundary_v002_vertices.csv"
_SOVEREIGN_PARTS = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_sovereign_parts_v001.csv"


@lru_cache(maxsize=1)
def _polygons() -> tuple[dict[str, object], ...]:
    vertices = csv_rows(_BOUNDARY_VERTICES)
    parts = {row["source_polygon_id"]: row for row in csv_rows(_SOVEREIGN_PARTS)}
    grouped: dict[str, list[tuple[int, Decimal, Decimal]]] = defaultdict(list)
    for row in vertices:
        grouped[row["polygon_id"]].append((int(row["vertex_sequence"]), Decimal(row["longitude"]), Decimal(row["latitude"])))
    out = []
    for polygon_id, points in grouped.items():
        points.sort()
        coords = [(lon, lat) for _, lon, lat in points]
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])
        part = parts[polygon_id]
        out.append({
            "polygon_id": polygon_id,
            "sovereign_part_id": part["sovereign_part_id"],
            "coords": tuple(coords),
            "min_lon": Decimal(part["min_longitude"]),
            "max_lon": Decimal(part["max_longitude"]),
            "min_lat": Decimal(part["min_latitude"]),
            "max_lat": Decimal(part["max_latitude"]),
        })
    return tuple(sorted(out, key=lambda x: str(x["polygon_id"])))


def _on_segment(px: Decimal, py: Decimal, ax: Decimal, ay: Decimal, bx: Decimal, by: Decimal) -> bool:
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if cross != 0:
        return False
    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)


def _point_relation(px: Decimal, py: Decimal, polygon: tuple[tuple[Decimal, Decimal], ...]) -> str:
    inside = False
    for index in range(len(polygon) - 1):
        ax, ay = polygon[index]
        bx, by = polygon[index + 1]
        if _on_segment(px, py, ax, ay, bx, by):
            return "BOUNDARY"
        if (ay > py) != (by > py):
            x_intersection = ax + (py - ay) * (bx - ax) / (by - ay)
            if x_intersection == px:
                return "BOUNDARY"
            if x_intersection > px:
                inside = not inside
    return "INSIDE" if inside else "OUTSIDE"


def _overall_extent(polygons: tuple[dict[str, object], ...]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return (
        min(item["min_lon"] for item in polygons),
        max(item["max_lon"] for item in polygons),
        min(item["min_lat"] for item in polygons),
        max(item["max_lat"] for item in polygons),
    )


@lru_cache(maxsize=1)
def derive_containment_qualifications() -> tuple[ContainmentQualification, ...]:
    polygons = _polygons()
    min_lon, max_lon, min_lat, max_lat = _overall_extent(polygons)
    manifest = {entry.source_file_id: entry for entry in load_manifest()}
    occurrence_families: dict[tuple[Decimal, Decimal], set[str]] = defaultdict(set)
    occurrence_files: dict[tuple[Decimal, Decimal], set[str]] = defaultdict(set)
    for item in derive_coordinate_occurrences():
        key = (item.source_longitude_numeric, item.source_latitude_numeric)
        occurrence_families[key].add(manifest[item.source_file_id].source_family)
        occurrence_files[key].add(item.source_file_id)

    out: list[ContainmentQualification] = []
    for index, candidate in enumerate(derive_coordinate_candidates(), start=1):
        lon = candidate.canonical_longitude
        lat = candidate.canonical_latitude
        in_extent = min_lon <= lon <= max_lon and min_lat <= lat <= max_lat
        part_id = ""
        raw_relation = "OUTSIDE"
        if in_extent:
            for polygon in polygons:
                if not (polygon["min_lon"] <= lon <= polygon["max_lon"] and polygon["min_lat"] <= lat <= polygon["max_lat"]):
                    continue
                relation = _point_relation(lon, lat, polygon["coords"])
                if relation == "BOUNDARY":
                    raw_relation = relation
                    part_id = str(polygon["sovereign_part_id"])
                    break
                if relation == "INSIDE":
                    raw_relation = relation
                    part_id = str(polygon["sovereign_part_id"])
                    break

        key = (lon, lat)
        families = occurrence_families.get(key, set())
        files = occurrence_files.get(key, set())
        marine_only = bool(families) and families <= {"05_new_waters_ocean"}
        if not in_extent:
            land_relation = SovereignLandRelation.OUTSIDE_GOVERNED_MAP_EXTENT
            context = "OUTSIDE_GOVERNED_MAP_EXTENT"
            status = "FAIL"
        elif raw_relation == "BOUNDARY":
            land_relation = SovereignLandRelation.ON_SOVEREIGN_BOUNDARY
            context = "BOUNDARY_EVIDENCE" if "NG-SPFILE-010" in files else "LAND_OR_MARINE_BOUNDARY"
            status = "PASS"
        elif raw_relation == "INSIDE":
            land_relation = SovereignLandRelation.INSIDE_SOVEREIGN_LAND
            context = "SOVEREIGN_LAND"
            status = "PASS"
        elif marine_only:
            land_relation = SovereignLandRelation.OUTSIDE_LAND_EXPECTED_MARINE_CANDIDATE
            context = "MARINE_SOURCE_EXPECTED"
            status = "PASS"
        else:
            land_relation = SovereignLandRelation.OUTSIDE_LAND_UNEXPECTED
            context = "UNEXPECTED_OUTSIDE_LAND"
            status = "FAIL"

        out.append(ContainmentQualification(
            containment_qualification_id=f"NG-CONT-{index:07d}",
            coordinate_candidate_id=candidate.coordinate_candidate_id,
            canonical_longitude=lon,
            canonical_latitude=lat,
            boundary_id="boundary:novegeo:sovereign",
            boundary_version=2,
            map_extent_status="WITHIN_GOVERNED_EXTENT" if in_extent else "OUTSIDE_GOVERNED_EXTENT",
            sovereign_land_relation=land_relation,
            sovereign_part_id=part_id,
            boundary_relation={"BOUNDARY": "TOUCHES", "INSIDE": "WITHIN", "OUTSIDE": "OUTSIDE"}[raw_relation],
            expected_spatial_context=context,
            qualification_status=status,
            qualification_basis="ACTUAL_BOUNDARY_V002_MULTIPOLYGON_POINT_RELATION_NOT_RECTANGULAR_EXTENT_ONLY",
        ))
    return tuple(out)


def containment_findings(rows: tuple[ContainmentQualification, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_containment_qualifications()
    return tuple(
        f"{row.coordinate_candidate_id}:{row.sovereign_land_relation.value}"
        for row in current if row.qualification_status != "PASS"
    )


__all__ = ["derive_containment_qualifications", "containment_findings"]
