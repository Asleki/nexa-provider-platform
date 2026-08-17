"""Shared constants and deterministic helpers for P006.7.11.7 Bundle 17E."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "data" / "novegeo" / "nngla" / "spatial-fabric" / "source"

COORDINATE_CANDIDATES_PATH = SOURCE_ROOT / "05_spatial_candidates" / "novegeo_coordinate_candidates_v002.csv"
OCCURRENCE_CROSSWALK_PATH = SOURCE_ROOT / "08_relationships" / "novegeo_coordinate_occurrence_crosswalk_v002.csv"
ENVIRONMENT_BINDINGS_PATH = SOURCE_ROOT / "08_relationships" / "novegeo_spatial_environment_bindings_v002.csv"
OCCUPANCY_RELATIONSHIPS_PATH = SOURCE_ROOT / "08_relationships" / "novegeo_spatial_occupancy_relationships_v002.csv"
CONTAINMENT_PATH = SOURCE_ROOT / "06_spatial_qualification" / "novegeo_spatial_containment_qualification_v002.csv"
PRECISION_PATH = SOURCE_ROOT / "06_spatial_qualification" / "novegeo_spatial_precision_qualification_v002.csv"
SOURCE_FIDELITY_PATH = SOURCE_ROOT / "10_evidence" / "novegeo_spatial_source_fidelity_results_v002.csv"
TOPOLOGY_QUALIFICATION_PATH = SOURCE_ROOT / "10_evidence" / "novegeo_spatial_topology_qualification_results_v001.csv"
CONFLICT_QUALIFICATION_PATH = SOURCE_ROOT / "10_evidence" / "novegeo_spatial_conflict_qualification_results_v001.csv"
MARINE_QUALIFICATION_PATH = SOURCE_ROOT / "10_evidence" / "novegeo_marine_spatial_qualification_results_v001.csv"
GRID_POINTS_PATH = SOURCE_ROOT / "01_spatial_fabric" / "novegeo_spatial_grid_points_v001.csv"
GEOMETRY_VERSION_CANDIDATES_PATH = (
    ROOT / "data" / "novegeo" / "nngla" / "geometry-roads-addresses" / "source" / "05_geographic_candidates" / "geometry_version_candidates.csv"
)
MIGRATION_MANIFEST_PATH = ROOT / "database" / "migrations" / "migration_manifest.json"
BUNDLE17E_INPUT_PATHS = (
    COORDINATE_CANDIDATES_PATH, OCCURRENCE_CROSSWALK_PATH, ENVIRONMENT_BINDINGS_PATH, OCCUPANCY_RELATIONSHIPS_PATH,
    CONTAINMENT_PATH, PRECISION_PATH, SOURCE_FIDELITY_PATH, TOPOLOGY_QUALIFICATION_PATH, CONFLICT_QUALIFICATION_PATH,
    MARINE_QUALIFICATION_PATH, GEOMETRY_VERSION_CANDIDATES_PATH,
)

BUNDLE_EFFECTIVE_DATE = "2026-08-17"
BASE_REPOSITORY_REVISION = "2cba0f3a44fee22cdb77752387ae7725a66bb3f1"
SPATIAL_DATASET_ID = "dataset:novegeo:spatial-fabric:coordinate-candidates"
SPATIAL_DATASET_VERSION = "2"
RUNTIME_MODE = "production"
EFFECT_SCOPE = "SHARED_REFERENCE"
REQUIRED_SCHEMA_CAPABILITIES = frozenset({
    "nngla_execution_foundation",
    "nngla_spatial_feature",
    "nngla_geometry_version",
    "nngla_geometry_authority_record",
    "nngla_canonical_crosswalk",
})


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def sha256_path(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}{sha256(payload).hexdigest()}"


def payload_sha256(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def truth(value: object) -> bool:
    return str(value).strip().lower() == "true"


def sequence_from_id(value: str) -> int:
    return int(str(value).rsplit("-", 1)[1])


__all__ = [
    "ROOT", "SOURCE_ROOT", "COORDINATE_CANDIDATES_PATH", "OCCURRENCE_CROSSWALK_PATH",
    "ENVIRONMENT_BINDINGS_PATH", "OCCUPANCY_RELATIONSHIPS_PATH", "CONTAINMENT_PATH", "PRECISION_PATH",
    "SOURCE_FIDELITY_PATH", "TOPOLOGY_QUALIFICATION_PATH", "CONFLICT_QUALIFICATION_PATH", "MARINE_QUALIFICATION_PATH", "GRID_POINTS_PATH",
    "GEOMETRY_VERSION_CANDIDATES_PATH", "MIGRATION_MANIFEST_PATH", "BUNDLE17E_INPUT_PATHS", "BUNDLE_EFFECTIVE_DATE",
    "BASE_REPOSITORY_REVISION", "SPATIAL_DATASET_ID", "SPATIAL_DATASET_VERSION", "RUNTIME_MODE", "EFFECT_SCOPE",
    "REQUIRED_SCHEMA_CAPABILITIES", "csv_rows", "sha256_path", "stable_id", "payload_sha256", "truth", "sequence_from_id",
]
