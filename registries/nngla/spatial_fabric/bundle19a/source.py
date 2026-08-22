"""Source loading and locked-baseline reconciliation for Bundle 19A."""
from __future__ import annotations

from functools import lru_cache

from collections import Counter, defaultdict
import json

from ._shared import (
    CANONICAL_ALIGNMENT_PATH,
    CONTAINMENT_PATH,
    COORDINATE_CANDIDATES_PATH,
    EFFECT_SCOPE,
    ENVIRONMENT_BINDINGS_PATH,
    EXPECTED_PLACE_TYPE_COUNTS,
    EXPECTED_REGION_COUNTS,
    HYDROLOGY_PATH,
    ISLAND_POLICY_PATH,
    REGION_ANCHOR_POLICY_PATH,
    SETTLEMENT_NAME_CATALOGUE_PATH,
    SETTLEMENT_POLICY_PATH,
    SETTLEMENT_SITING_PATH,
    SOVEREIGN_PARTS_PATH,
    SOVEREIGN_VERTICES_PATH,
    SPATIAL_CROSSWALK_PATH,
    csv_rows,
)
from .contracts import SettlementSitingRequirement, SpatialSupportPoint


@lru_cache(maxsize=1)
def load_settlement_requirements() -> tuple[SettlementSitingRequirement, ...]:
    siting = csv_rows(SETTLEMENT_SITING_PATH)
    alignment = {
        row["source_record_id"]: row
        for row in csv_rows(CANONICAL_ALIGNMENT_PATH)
        if row["object_family"] == "PLACE"
    }
    names = {row["source_place_code"]: row for row in csv_rows(SETTLEMENT_NAME_CATALOGUE_PATH)}
    rows: list[SettlementSitingRequirement] = []
    for row in siting:
        source_place = row["source_place_code"]
        aligned = alignment.get(source_place)
        name = names.get(source_place)
        if aligned is None or name is None:
            raise ValueError(f"missing canonical alignment/name catalogue record for {source_place}")
        if aligned["candidate_id"] != name["settlement_name_record_id"]:
            raise ValueError(f"settlement-name identity mismatch for {source_place}")
        if aligned["geometry_status"] != "NO_ASSOCIABLE_GEOMETRY_SOURCE":
            raise ValueError(f"unexpected pre-existing geometry status for {source_place}")
        if name["spatial_assignment_status"] != "UNMAPPED_PENDING_ASSOCIATION":
            raise ValueError(f"place {source_place} is no longer an unmapped Bundle 19A input")
        rows.append(SettlementSitingRequirement(
            source_place_code=source_place,
            place_id=aligned["canonical_id"],
            settlement_name_record_id=name["settlement_name_record_id"],
            canonical_name=row["canonical_name"],
            place_type_code=row["place_type_code"],
            settlement_scale=row["settlement_scale"],
            urbanity=row["urbanity"],
            parent_source_place_code=row["parent_source_place_code"],
            major_city_source_place_code=row["major_city_source_place_code"],
            region_code=row["region_code"],
            region_name=row["region_name"],
            terrain_zone_code=row["terrain_zone_code"],
            location_character=row["location_character"],
            dominant_function=row["dominant_function"],
            source_dataset_id=row["source_dataset_id"],
            source_sha256=row["source_sha256"],
            runtime_effect_scope=row["runtime_effect_scope"],
        ))
    rows.sort(key=lambda item: int(item.source_place_code.rsplit("-", 1)[1]))
    qualify_locked_place_baseline(tuple(rows))
    return tuple(rows)


def qualify_locked_place_baseline(rows: tuple[SettlementSitingRequirement, ...]) -> None:
    if len(rows) != 700:
        raise ValueError(f"Bundle 19A requires exactly 700 canonical places, found {len(rows)}")
    if len({row.source_place_code for row in rows}) != 700 or len({row.place_id for row in rows}) != 700:
        raise ValueError("place/source identities must remain one-to-one and unique")
    place_counts = Counter(row.place_type_code for row in rows)
    region_counts = Counter(row.region_code for row in rows)
    if dict(place_counts) != EXPECTED_PLACE_TYPE_COUNTS:
        raise ValueError(f"place-type baseline changed: {dict(place_counts)}")
    if dict(region_counts) != EXPECTED_REGION_COUNTS:
        raise ValueError(f"regional place baseline changed: {dict(region_counts)}")
    for ordinal, row in enumerate(rows, start=1):
        expected_source = f"NGP-{ordinal:06d}"
        expected_place = f"NG-PLC-{ordinal:06d}"
        if row.source_place_code != expected_source or row.place_id != expected_place:
            raise ValueError(f"locked suffix allocation changed at ordinal {ordinal}")
        if row.runtime_effect_scope != EFFECT_SCOPE:
            raise ValueError("place runtime effect scope changed")


@lru_cache(maxsize=1)
def load_support_points() -> tuple[SpatialSupportPoint, ...]:
    coordinates = {row["coordinate_candidate_id"]: row for row in csv_rows(COORDINATE_CANDIDATES_PATH)}
    containment = {row["coordinate_candidate_id"]: row for row in csv_rows(CONTAINMENT_PATH)}
    crosswalk = {row["coordinate_candidate_id"]: row for row in csv_rows(SPATIAL_CROSSWALK_PATH)}
    environment = {row["spatial_point_id"]: row for row in csv_rows(ENVIRONMENT_BINDINGS_PATH)}
    if not (len(coordinates) == len(containment) == len(crosswalk) == 2411):
        raise ValueError("canonical spatial infrastructure must reconcile exactly 2,411 coordinate records")
    rows: list[SpatialSupportPoint] = []
    for candidate_id, coord in coordinates.items():
        contain = containment.get(candidate_id)
        cross = crosswalk.get(candidate_id)
        if contain is None or cross is None:
            raise ValueError(f"incomplete canonical spatial reconciliation for {candidate_id}")
        if contain["qualification_status"] != "PASS":
            continue
        if contain["sovereign_land_relation"] != "INSIDE_SOVEREIGN_LAND":
            continue
        spatial_id = cross["canonical_spatial_point_id"]
        env = environment.get(spatial_id, {})
        rows.append(SpatialSupportPoint(
            spatial_point_id=spatial_id,
            longitude=float(coord["canonical_longitude"]),
            latitude=float(coord["canonical_latitude"]),
            sovereign_part_id=contain["sovereign_part_id"],
            sovereign_land_relation=contain["sovereign_land_relation"],
            terrain_class=env.get("terrain_class", ""),
            elevation_m=float(env["elevation_m"]) if env.get("elevation_m") else None,
            annual_rainfall_mm=float(env["annual_rainfall_mm"]) if env.get("annual_rainfall_mm") else None,
            climate_class=env.get("climate_class", ""),
            vegetation_class=env.get("vegetation_class", ""),
            aridity_class=env.get("aridity_class", ""),
            hydrology_reference_id=env.get("hydrology_reference_id", ""),
        ))
    rows.sort(key=lambda item: int(item.spatial_point_id.rsplit("-", 1)[1]))
    if len(rows) != 1348:
        raise ValueError(f"expected 1,348 interior sovereign support points, found {len(rows)}")
    return tuple(rows)


@lru_cache(maxsize=1)
def load_sovereign_polygons() -> tuple[dict[str, object], ...]:
    parts = {row["source_polygon_id"]: row for row in csv_rows(SOVEREIGN_PARTS_PATH)}
    grouped: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in csv_rows(SOVEREIGN_VERTICES_PATH):
        grouped[row["polygon_id"]].append((int(row["vertex_sequence"]), float(row["longitude"]), float(row["latitude"])))
    polygons: list[dict[str, object]] = []
    for polygon_id, vertices in grouped.items():
        vertices.sort(key=lambda item: item[0])
        ring = tuple((lon, lat) for _, lon, lat in vertices)
        if ring and ring[0] != ring[-1]:
            ring = ring + (ring[0],)
        part = parts[polygon_id]
        polygons.append({
            "polygon_id": polygon_id,
            "sovereign_part_id": part["sovereign_part_id"],
            "ring": ring,
            "min_lon": float(part["min_longitude"]),
            "max_lon": float(part["max_longitude"]),
            "min_lat": float(part["min_latitude"]),
            "max_lat": float(part["max_latitude"]),
        })
    polygons.sort(key=lambda item: str(item["sovereign_part_id"]))
    if len(polygons) != 6:
        raise ValueError("sovereign boundary v002 must contain mainland plus five offshore parts")
    return tuple(polygons)


@lru_cache(maxsize=1)
def load_lake_polygons() -> tuple[dict[str, object], ...]:
    payload = json.loads(HYDROLOGY_PATH.read_text(encoding="utf-8"))
    lakes: list[dict[str, object]] = []
    for lake in payload.get("lakes", []):
        geometry = lake.get("geometry", {})
        if geometry.get("type") != "Polygon":
            continue
        coordinates = geometry.get("coordinates", [])
        if not coordinates:
            continue
        ring = tuple((float(point[0]), float(point[1])) for point in coordinates[0])
        if ring and ring[0] != ring[-1]:
            ring = ring + (ring[0],)
        ref = lake.get("referencePoint", {})
        lakes.append({
            "lake_id": lake["lakeId"],
            "ring": ring,
            "reference_longitude": float(ref.get("longitude", 0.0)),
            "reference_latitude": float(ref.get("latitude", 0.0)),
        })
    if len(lakes) != 3:
        raise ValueError("Bundle 19A expects the three qualified closed-basin lakes")
    return tuple(lakes)


@lru_cache(maxsize=1)
def load_region_anchor_policy() -> tuple[dict[str, str], ...]:
    rows = csv_rows(REGION_ANCHOR_POLICY_PATH)
    if len(rows) != 8 or {row["region_code"] for row in rows} != set(EXPECTED_REGION_COUNTS):
        raise ValueError("region anchor policy must define exactly the eight NoveGeo regions")
    if any(row["policy_status"] != "ACTIVE" or row["runtime_effect_scope"] != EFFECT_SCOPE for row in rows):
        raise ValueError("region anchor policy contains inactive or non-shared rows")
    return rows


@lru_cache(maxsize=1)
def load_settlement_policy() -> dict[str, dict[str, str]]:
    rows = csv_rows(SETTLEMENT_POLICY_PATH)
    result = {row["place_type_code"]: row for row in rows}
    if set(result) != set(EXPECTED_PLACE_TYPE_COUNTS) or len(result) != len(rows):
        raise ValueError("settlement spatial policy must define every and only canonical place type")
    if any(row["policy_status"] != "ACTIVE" or row["runtime_effect_scope"] != EFFECT_SCOPE for row in rows):
        raise ValueError("settlement spatial policy contains inactive or non-shared rows")
    return result


@lru_cache(maxsize=1)
def load_island_policy() -> dict[str, dict[str, str]]:
    rows = csv_rows(ISLAND_POLICY_PATH)
    result = {row["source_place_code"]: row for row in rows}
    if len(result) != 8 or len(result) != len(rows):
        raise ValueError("island assignment policy must define exactly eight island settlements")
    if any(row["policy_status"] != "ACTIVE" or row["runtime_effect_scope"] != EFFECT_SCOPE for row in rows):
        raise ValueError("island policy contains inactive or non-shared rows")
    return result


__all__ = [
    "load_settlement_requirements", "qualify_locked_place_baseline", "load_support_points",
    "load_sovereign_polygons", "load_lake_polygons", "load_region_anchor_policy",
    "load_settlement_policy", "load_island_policy",
]
