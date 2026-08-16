"""Bundle 17A deterministic coordinate occurrence and candidate derivation."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import csv

from .contracts import (
    COORDINATE_FIELD_PAIRS,
    CoordinateCandidate,
    CoordinateOccurrence,
    canonical_decimal_text,
    parse_decimal,
)
from .contracts import SpatialSourceManifestEntry
from .source_inventory import load_manifest, source_path


_PRIMARY_ID_FIELDS = (
    "climate_observation_id", "elevation_observation_id", "vegetation_observation_id",
    "rainfall_system_id", "sovereign_part_id", "spatial_cell_id", "spatial_point_id",
    "junction_id", "island_candidate_id", "lake_candidate_id", "landform_reference_id",
    "river_candidate_id", "candidate_id", "boundary_request_id", "alignment_request_id",
    "siting_request_id", "connection_id", "island_state_record_id", "marine_interface_id",
    "anchor_id", "route_candidate_id", "marine_waterbody_id", "name_id",
)
_PARENT_FIELDS = (
    ("route_candidate_id", "SEA_ROUTE"),
    ("feature_candidate_id", "GEOGRAPHIC_FEATURE"),
    ("island_candidate_id", "ISLAND"),
    ("lake_candidate_id", "LAKE"),
    ("river_candidate_id", "RIVER"),
    ("marine_interface_id", "MARINE_INTERFACE"),
    ("rainfall_system_id", "RAINFALL_SYSTEM"),
    ("spatial_cell_id", "SPATIAL_CELL"),
    ("spatial_point_id", "SPATIAL_POINT"),
    ("landform_reference_id", "LANDFORM"),
    ("junction_id", "HYDROLOGY_JUNCTION"),
    ("candidate_id", "FEATURE_CANDIDATE"),
    ("sovereign_part_id", "SOVEREIGN_PART"),
)


def _csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def _record_identity(row: dict[str, str], row_number: int) -> str:
    base = ""
    for field in _PRIMARY_ID_FIELDS:
        if str(row.get(field, "")).strip():
            base = str(row[field]).strip()
            break
    if not base and row.get("polygon_id"):
        base = f"{row['polygon_id']}:{row.get('ring_id', '')}"
    if not base:
        base = f"row:{row_number}"
    if str(row.get("vertex_sequence", "")).strip():
        base += f":vertex:{row.get('ring_id', '')}:{row['vertex_sequence']}"
    return base


def _parent(row: dict[str, str]) -> tuple[str, str]:
    for field, kind in _PARENT_FIELDS:
        value = str(row.get(field, "")).strip()
        if value:
            return kind, value
    if row.get("polygon_id"):
        return "SOVEREIGN_BOUNDARY_PART", str(row["polygon_id"]).strip()
    return "SOURCE_RECORD", ""


def _source_crs(row: dict[str, str]) -> str:
    value = str(row.get("crs_code", "")).strip()
    return value or "UNDECLARED_IN_ROW"


def _geometry_role(row: dict[str, str], pair_role: str) -> str:
    if pair_role in {"SEGMENT_START", "SEGMENT_END", "REFERENCE_CENTRE", "REFERENCE_POINT", "CANDIDATE_REFERENCE_POINT"}:
        return pair_role
    return str(row.get("vertex_role", "")).strip() or "POINT_OBSERVATION"


def _hash_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}{sha256(payload).hexdigest()}"


def derive_coordinate_occurrences(
    entries: tuple[SpatialSourceManifestEntry, ...] | None = None,
) -> tuple[CoordinateOccurrence, ...]:
    manifest = entries or load_manifest()
    out: list[CoordinateOccurrence] = []
    for entry in manifest:
        if not entry.contains_coordinates:
            continue
        path = source_path(entry)
        rows = _csv_rows(path)
        for row_number, row in enumerate(rows, start=2):
            source_record_id = _record_identity(row, row_number)
            parent_type, parent_id = _parent(row)
            for lon_field, lat_field, pair_role in COORDINATE_FIELD_PAIRS:
                lon_text = str(row.get(lon_field, "")).strip()
                lat_text = str(row.get(lat_field, "")).strip()
                if not lon_text and not lat_text:
                    continue
                if not lon_text or not lat_text:
                    raise ValueError(
                        f"partial coordinate pair in {entry.source_path} row {row_number}: {lon_field}/{lat_field}"
                    )
                lon = parse_decimal(lon_text)
                lat = parse_decimal(lat_text)
                occurrence_id = _hash_id(
                    "coordocc:nngla:", entry.source_file_id, source_record_id,
                    lon_field, lat_field, lon_text, lat_text,
                )
                out.append(CoordinateOccurrence(
                    coordinate_occurrence_id=occurrence_id,
                    source_file_id=entry.source_file_id,
                    source_record_id=source_record_id,
                    parent_object_type=parent_type,
                    parent_object_id=parent_id,
                    geometry_role=_geometry_role(row, pair_role),
                    ring_id=str(row.get("ring_id", "")).strip(),
                    vertex_sequence=str(row.get("vertex_sequence", "")).strip(),
                    source_longitude_text=lon_text,
                    source_latitude_text=lat_text,
                    source_longitude_numeric=lon,
                    source_latitude_numeric=lat,
                    crs_source_code=_source_crs(row),
                    source_version=entry.dataset_version,
                ))
    ids = [item.coordinate_occurrence_id for item in out]
    if len(ids) != len(set(ids)):
        raise ValueError("coordinate occurrence identity collision")
    return tuple(out)


def candidate_identity(longitude: Decimal, latitude: Decimal) -> str:
    return _hash_id(
        "coordcand:nngla:",
        "NG-CRS-EPSG4326",
        canonical_decimal_text(longitude),
        canonical_decimal_text(latitude),
    )


def derive_coordinate_candidates(
    occurrences: tuple[CoordinateOccurrence, ...] | None = None,
) -> tuple[CoordinateCandidate, ...]:
    current = occurrences or derive_coordinate_occurrences()
    counts = Counter((item.source_longitude_numeric, item.source_latitude_numeric) for item in current)
    candidates = tuple(
        CoordinateCandidate(
            coordinate_candidate_id=candidate_identity(lon, lat),
            canonical_longitude=lon,
            canonical_latitude=lat,
            governed_crs_code="NG-CRS-EPSG4326",
            occurrence_count=count,
            land_marine_classification="UNRESOLVED_PENDING_17B",
            canonicalization_status="CANDIDATE_ONLY_NOT_PERSISTED",
        )
        for (lon, lat), count in sorted(counts.items(), key=lambda item: (item[0][1], item[0][0]))
    )
    ids = [item.coordinate_candidate_id for item in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("coordinate candidate identity collision")
    return candidates


def occurrence_crosswalk_rows(
    occurrences: tuple[CoordinateOccurrence, ...] | None = None,
) -> tuple[dict[str, str], ...]:
    current = occurrences or derive_coordinate_occurrences()
    return tuple({
        "coordinate_occurrence_id": item.coordinate_occurrence_id,
        "coordinate_candidate_id": candidate_identity(item.source_longitude_numeric, item.source_latitude_numeric),
        "crosswalk_basis": "EXACT_NUMERIC_COORDINATE_EQUIVALENCE",
        "crosswalk_status": "MATCHED",
    } for item in current)


__all__ = [
    "derive_coordinate_occurrences",
    "derive_coordinate_candidates",
    "candidate_identity",
    "occurrence_crosswalk_rows",
]
