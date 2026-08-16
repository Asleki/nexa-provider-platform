"""Bundle 17B source-fidelity qualification for immutable spatial occurrences."""
from __future__ import annotations

from functools import lru_cache
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import csv

from registries.nngla.spatial_fabric import derive_coordinate_occurrences, load_manifest
from registries.nngla.spatial_fabric.source_inventory import source_path

from ._shared import (
    BOUNDARY_CANDIDATE_PATH,
    CLIMATE_QUALIFIED_PATH,
    HYDROLOGY_QUALIFIED_PATH,
    LANDFORMS_QUALIFIED_PATH,
    ROOT,
    TERRAIN_QUALIFIED_PATH,
    VEGETATION_QUALIFIED_PATH,
    csv_rows,
    file_sha256,
    json_value,
    recursively_collect_coordinate_pairs,
)
from .contracts import SourceFidelityResult
from .crs_reconciliation import crs_by_source_file


_PRIMARY_ID_FIELDS = (
    "climate_observation_id", "elevation_observation_id", "vegetation_observation_id",
    "rainfall_system_id", "sovereign_part_id", "spatial_cell_id", "spatial_point_id",
    "junction_id", "island_candidate_id", "lake_candidate_id", "landform_reference_id",
    "river_candidate_id", "candidate_id", "boundary_request_id", "alignment_request_id",
    "siting_request_id", "connection_id", "island_state_record_id", "marine_interface_id",
    "anchor_id", "route_candidate_id", "marine_waterbody_id", "name_id",
)


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


def _source_rows_by_occurrence(path: Path) -> dict[tuple[str, Decimal, Decimal], dict[str, str]]:
    rows = csv_rows(path)
    out: dict[tuple[str, Decimal, Decimal], dict[str, str]] = {}
    pairs = (
        ("longitude", "latitude"), ("centre_longitude", "centre_latitude"),
        ("reference_longitude", "reference_latitude"),
        ("candidate_reference_longitude", "candidate_reference_latitude"),
        ("start_longitude", "start_latitude"), ("end_longitude", "end_latitude"),
    )
    for row_number, row in enumerate(rows, start=2):
        identity = _record_identity(row, row_number)
        for lon_field, lat_field in pairs:
            lon = str(row.get(lon_field, "")).strip()
            lat = str(row.get(lat_field, "")).strip()
            if lon and lat:
                out[(identity, Decimal(lon), Decimal(lat))] = row
    return out


def _coordinate_pairs_from_csv(path: Path) -> set[tuple[Decimal, Decimal]]:
    pairs: set[tuple[Decimal, Decimal]] = set()
    for row in csv_rows(path):
        for lon_field, lat_field in (
            ("longitude", "latitude"), ("centre_longitude", "centre_latitude"),
            ("reference_longitude", "reference_latitude"),
            ("start_longitude", "start_latitude"), ("end_longitude", "end_latitude"),
        ):
            lon = str(row.get(lon_field, "")).strip()
            lat = str(row.get(lat_field, "")).strip()
            if lon and lat:
                pairs.add((Decimal(lon), Decimal(lat)))
    return pairs


def _coordinate_pairs(path: Path) -> set[tuple[Decimal, Decimal]]:
    if path.suffix.lower() == ".csv":
        return _coordinate_pairs_from_csv(path)
    return recursively_collect_coordinate_pairs(json_value(path))


def _fallback_parent(entry) -> Path | None:
    dataset = entry.dataset_id
    filename = entry.filename
    if dataset.startswith("dataset:novegeo:terrain:elevation") or filename == "novegeo_spatial_grid_cells_v001.csv":
        return TERRAIN_QUALIFIED_PATH
    if dataset.startswith("dataset:novegeo:climate:baseline"):
        return CLIMATE_QUALIFIED_PATH
    if dataset.startswith("dataset:novegeo:vegetation:baseline"):
        return VEGETATION_QUALIFIED_PATH
    if dataset.startswith("dataset:novegeo:hydrology:surface-water"):
        return HYDROLOGY_QUALIFIED_PATH
    if dataset.startswith("dataset:novegeo:landforms") or filename in {
        "novegeo_mountain_candidates_v001.csv", "novegeo_plain_candidates_v001.csv",
        "novegeo_plateau_candidates_v001.csv", "novegeo_valley_candidates_v001.csv",
    }:
        return LANDFORMS_QUALIFIED_PATH
    if "world_boundary" in filename or "sovereign_parts" in filename or "island_candidates" in filename:
        return BOUNDARY_CANDIDATE_PATH
    return None


def _core_attribute_indexes() -> dict[str, dict[tuple[Decimal, Decimal], dict]]:
    terrain = json_value(TERRAIN_QUALIFIED_PATH)
    climate = json_value(CLIMATE_QUALIFIED_PATH)
    vegetation = json_value(VEGETATION_QUALIFIED_PATH)
    return {
        "terrain": {(Decimal(str(x["longitude"])), Decimal(str(x["latitude"]))): x for x in terrain["samples"]},
        "climate": {(Decimal(str(x["longitude"])), Decimal(str(x["latitude"]))): x for x in climate["samples"]},
        "vegetation": {(Decimal(str(x["longitude"])), Decimal(str(x["latitude"]))): x for x in vegetation["samples"]},
    }


def _attribute_match(entry, row: dict[str, str], lon: Decimal, lat: Decimal, indexes) -> str:
    filename = entry.filename
    if filename in {"novegeo_elevation_observations_v001.csv", "novegeo_spatial_grid_points_v001.csv"}:
        sample = indexes["terrain"].get((lon, lat))
        if sample is None:
            return "MISMATCH"
        return "MATCHED" if (
            Decimal(str(sample["elevationMeters"])) == Decimal(row["elevation_m"])
            and str(sample["landformClass"]).upper() == row["terrain_class"].upper()
        ) else "MISMATCH"
    if filename == "novegeo_climate_observations_v001.csv":
        sample = indexes["climate"].get((lon, lat))
        if sample is None:
            return "MISMATCH"
        checks = (
            Decimal(str(sample["annualRainfallMm"])) == Decimal(row["annual_rainfall_mm"]),
            Decimal(str(sample["meanTemperatureC"])) == Decimal(row["mean_temperature_c"]),
            Decimal(str(sample["meanWindSpeedMps"])) == Decimal(row["mean_wind_speed_mps"]),
            Decimal(str(sample["prevailingWindDirectionDegrees"])) == Decimal(row["prevailing_wind_direction_deg"]),
            str(sample["climateClass"]).upper() == row["climate_class"].upper(),
        )
        return "MATCHED" if all(checks) else "MISMATCH"
    if filename == "novegeo_vegetation_observations_v001.csv":
        sample = indexes["vegetation"].get((lon, lat))
        if sample is None:
            return "MISMATCH"
        checks = (
            str(sample["vegetationClass"]).upper() == row["vegetation_class"].upper(),
            str(sample["aridityClass"]).upper() == row["aridity_class"].upper(),
            Decimal(str(sample["sourceAnnualRainfallMm"])) == Decimal(row["source_annual_rainfall_mm"]),
            Decimal(str(sample["sourceMeanTemperatureC"])) == Decimal(row["source_mean_temperature_c"]),
        )
        return "MATCHED" if all(checks) else "MISMATCH"
    return "NOT_APPLICABLE"


@lru_cache(maxsize=1)
def derive_source_fidelity_results() -> tuple[SourceFidelityResult, ...]:
    manifest = {entry.source_file_id: entry for entry in load_manifest()}
    crs = crs_by_source_file()
    occurrences = derive_coordinate_occurrences()
    row_maps: dict[str, dict[tuple[str, Decimal, Decimal], dict[str, str]]] = {}
    source_hashes: dict[str, str] = {}
    parent_pair_cache: dict[str, set[tuple[Decimal, Decimal]]] = {}
    parent_hash_cache: dict[str, str] = {}
    indexes = _core_attribute_indexes()
    out: list[SourceFidelityResult] = []

    for sequence, occurrence in enumerate(occurrences, start=1):
        entry = manifest[occurrence.source_file_id]
        path = source_path(entry)
        if entry.source_file_id not in row_maps:
            row_maps[entry.source_file_id] = _source_rows_by_occurrence(path)
        row_map = row_maps[entry.source_file_id]
        row = row_map.get((occurrence.source_record_id, occurrence.source_longitude_numeric, occurrence.source_latitude_numeric))
        findings: list[str] = []
        if row is None:
            findings.append("SOURCE_RECORD_NOT_FOUND")
            row = {}
        if entry.source_file_id not in source_hashes:
            source_hashes[entry.source_file_id] = file_sha256(path)
        actual_source_hash = source_hashes[entry.source_file_id]
        if actual_source_hash != entry.source_sha256:
            findings.append("SOURCE_FILE_SHA256_MISMATCH")

        parent_text = str(row.get("source_path_reference", "")).strip()
        parent_path = ROOT / parent_text if parent_text else _fallback_parent(entry)
        parent_hash_ok = True
        parent_pairs: set[tuple[Decimal, Decimal]] | None = None
        if parent_path is not None and parent_path.is_file():
            parent_key = str(parent_path)
            if parent_key not in parent_hash_cache:
                parent_hash_cache[parent_key] = file_sha256(parent_path)
            parent_hash = parent_hash_cache[parent_key]
            expected_parent_hash = str(row.get("source_sha256", "")).strip()
            if expected_parent_hash and parent_hash != expected_parent_hash:
                parent_hash_ok = False
                findings.append("PARENT_SOURCE_SHA256_MISMATCH")
            if parent_path.suffix.lower() in {".json", ".geojson", ".csv"}:
                if parent_key not in parent_pair_cache:
                    parent_pair_cache[parent_key] = _coordinate_pairs(parent_path)
                parent_pairs = parent_pair_cache[parent_key]
        elif parent_text:
            parent_hash_ok = False
            findings.append("PARENT_SOURCE_MISSING")

        key = (occurrence.source_longitude_numeric, occurrence.source_latitude_numeric)
        coordinate_match = "SOURCE_FILE_HASH_ONLY"
        if entry.filename == "novegeo_spatial_grid_cells_v001.csv":
            coordinate_match = "MATCHED" if key in _coordinate_pairs(TERRAIN_QUALIFIED_PATH) else "MISMATCH"
        elif entry.filename == "novegeo_sea_route_vertices_v001.csv":
            coordinate_match = "DECLARED_DERIVATION_NOT_RECOMPUTED_17B"
        elif entry.filename == "novegeo_sovereign_parts_v001.csv":
            coordinate_match = "DERIVED_REFERENCE_NOT_EXPECTED_EXACT"
        elif parent_pairs is not None:
            coordinate_match = "MATCHED" if key in parent_pairs else "DERIVED_REFERENCE_NOT_EXPECTED_EXACT"

        attribute_match = _attribute_match(entry, row, *key, indexes)
        if coordinate_match == "MISMATCH":
            findings.append("SOURCE_COORDINATE_MISMATCH")
        if attribute_match == "MISMATCH":
            findings.append("SOURCE_ATTRIBUTE_MISMATCH")

        row_dataset = str(row.get("source_dataset_id", "")).strip()
        if row_dataset:
            dataset_lineage = "MATCHED" if row_dataset == entry.dataset_id else "MISMATCH"
        else:
            dataset_lineage = "DECLARED_BY_MANIFEST_OR_DERIVATION"
        if dataset_lineage == "MISMATCH":
            findings.append("DATASET_LINEAGE_MISMATCH")

        crs_lineage = "MATCHED" if occurrence.source_file_id in crs else "MISSING"
        if crs_lineage != "MATCHED":
            findings.append("CRS_LINEAGE_MISSING")
        if not parent_hash_ok:
            findings.append("PARENT_HASH_NOT_QUALIFIED")

        out.append(SourceFidelityResult(
            source_fidelity_result_id=f"NG-FID-{sequence:08d}",
            coordinate_occurrence_id=occurrence.coordinate_occurrence_id,
            source_file_id=occurrence.source_file_id,
            source_record_id=occurrence.source_record_id,
            source_dataset_id=entry.dataset_id,
            source_dataset_version=entry.dataset_version,
            source_path_reference=parent_text or entry.source_path,
            expected_source_sha256=entry.source_sha256,
            actual_source_sha256=actual_source_hash,
            source_coordinate_match=coordinate_match,
            source_attribute_match=attribute_match,
            dataset_lineage_match=dataset_lineage,
            crs_lineage_match=crs_lineage,
            fidelity_status="PASS" if not findings else "FAIL",
            findings=";".join(findings),
        ))
    return tuple(out)


def source_fidelity_findings(rows: tuple[SourceFidelityResult, ...] | None = None) -> tuple[str, ...]:
    current = rows or derive_source_fidelity_results()
    return tuple(f"{row.source_fidelity_result_id}:{row.findings}" for row in current if row.fidelity_status != "PASS")


__all__ = ["derive_source_fidelity_results", "source_fidelity_findings"]
