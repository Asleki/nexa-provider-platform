"""Read-only Bundle 14B migration-source snapshot loader."""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path
from .source_dataset import (
    DataClassification, DatasetClass, MigrationEligibility,
    SourceArtifactEvidence, SourceDatasetManifestEntry, ValidationEvidence,
)

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "novegeo" / "nngla" / "ingest-foundation" / "source"


def _rows(relative_path: str, root: Path = DEFAULT_SOURCE_ROOT):
    with (root / relative_path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _bool(value: str) -> bool:
    value = value.strip().lower()
    if value not in {"true", "false"}:
        raise ValueError(f"invalid boolean {value!r}")
    return value == "true"


def load_manifest(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(SourceDatasetManifestEntry(
        r["catalogue_id"], r["folder_family"], r["file_name"], int(r["row_count"]),
        DatasetClass(r["dataset_class"]), MigrationEligibility(r["migration_eligibility"]),
        r["source_basis"], _bool(r["spatial_dependency"]), r["status"],
    ) for r in _rows("00_manifest/csv_catalogue_manifest.csv", root))


def load_data_classifications(root: Path = DEFAULT_SOURCE_ROOT):
    rows = _rows("03_authority_identifiers/novegeo_data_classification_register.csv", root)
    return {DataClassification(r["classification_code"]): dict(r) for r in rows}


def load_crs_rows(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(_rows("02_controlled_codes/coordinate_reference_systems.csv", root))


def load_geometry_type_rows(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(_rows("02_controlled_codes/geometry_type_codes.csv", root))


def load_candidate_rows(relative_path: str, root: Path = DEFAULT_SOURCE_ROOT):
    allowed = {
        "05_geographic_candidates/geographic_feature_candidates.csv",
        "05_geographic_candidates/geometry_version_candidates.csv",
        "05_geographic_candidates/administrative_area_candidates.csv",
        "05_geographic_candidates/survey_control_point_candidates.csv",
        "06_roads_addresses/road_reference_candidates.csv",
        "06_roads_addresses/address_reference_candidates.csv",
        "07_land/parcel_bootstrap.csv",
        "07_land/title_bootstrap.csv",
        "07_land/state_land_bootstrap.csv",
        "09_quarantine/invalid_geographic_feature_candidates.csv",
    }
    if relative_path not in allowed:
        raise ValueError("relative_path is not part of the Bundle 14B governed candidate snapshot")
    return tuple(_rows(relative_path, root))


def load_validation_evidence(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(ValidationEvidence(
        r["validation_id"], r["file_path"], r["validation_type"], int(r["row_count"]) if r["row_count"] else None,
        r["result"], int(r["error_count"]), r["details"], date.fromisoformat(r["validated_at"]),
    ) for r in _rows("10_evidence/novegeo_validation_evidence_register.csv", root))


def load_file_hashes(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(SourceArtifactEvidence(
        r["hash_record_id"], r["file_path"], r["sha256"], int(r["byte_size"]), date.fromisoformat(r["calculated_at"]),
    ) for r in _rows("10_evidence/novegeo_file_hash_register.csv", root))


__all__ = [
    "DEFAULT_SOURCE_ROOT", "load_manifest", "load_data_classifications", "load_crs_rows",
    "load_geometry_type_rows", "load_candidate_rows", "load_validation_evidence", "load_file_hashes",
]
