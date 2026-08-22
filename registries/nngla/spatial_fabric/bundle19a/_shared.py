"""Shared paths and deterministic helpers for P006.7.11.10 / Bundle 19A."""
from __future__ import annotations

from csv import DictReader
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[4]
SPATIAL_ROOT = ROOT / "data" / "novegeo" / "nngla" / "spatial-fabric"
LOCKED_SOURCE_ROOT = SPATIAL_ROOT / "source"
BUNDLE_ROOT = SPATIAL_ROOT / "bundle19a"
CONTROL_ROOT = BUNDLE_ROOT / "controlled"
QUALIFIED_ROOT = BUNDLE_ROOT / "qualified"
RELATIONSHIP_ROOT = BUNDLE_ROOT / "relationships"
EVIDENCE_ROOT = BUNDLE_ROOT / "evidence"

SETTLEMENT_SITING_PATH = LOCKED_SOURCE_ROOT / "04_settlements_roads_administration" / "novegeo_settlement_siting_candidates_v001.csv"
CANONICAL_ALIGNMENT_PATH = LOCKED_SOURCE_ROOT / "08_relationships" / "novegeo_existing_canonical_alignment_v002.csv"
COORDINATE_CANDIDATES_PATH = LOCKED_SOURCE_ROOT / "05_spatial_candidates" / "novegeo_coordinate_candidates_v002.csv"
CONTAINMENT_PATH = LOCKED_SOURCE_ROOT / "06_spatial_qualification" / "novegeo_spatial_containment_qualification_v002.csv"
SPATIAL_CROSSWALK_PATH = LOCKED_SOURCE_ROOT / "08_relationships" / "novegeo_spatial_canonical_crosswalk_v001.csv"
ENVIRONMENT_BINDINGS_PATH = LOCKED_SOURCE_ROOT / "08_relationships" / "novegeo_spatial_environment_bindings_v002.csv"
SOVEREIGN_VERTICES_PATH = LOCKED_SOURCE_ROOT / "01_spatial_fabric" / "novegeo_world_boundary_v002_vertices.csv"
SOVEREIGN_PARTS_PATH = LOCKED_SOURCE_ROOT / "01_spatial_fabric" / "novegeo_sovereign_parts_v001.csv"
SETTLEMENT_NAME_CATALOGUE_PATH = ROOT / "data" / "novegeo" / "nngla" / "geographic-identity-places" / "source" / "04_name_catalogues" / "settlement_name_catalogue.csv"
HYDROLOGY_PATH = ROOT / "data" / "novegeo" / "geography" / "hydrology" / "qualified" / "novegeo_hydrology_v001.json"
WORLD_BOUNDARY_GEOJSON_PATH = ROOT / "data" / "novegeo" / "geography" / "world-boundary" / "candidate" / "novegeo_world_boundary_v002.geojson"

REGION_ANCHOR_POLICY_PATH = CONTROL_ROOT / "novegeo_region_spatial_anchor_policy_v001.csv"
SETTLEMENT_POLICY_PATH = CONTROL_ROOT / "novegeo_settlement_spatial_policy_v001.csv"
ISLAND_POLICY_PATH = CONTROL_ROOT / "novegeo_island_settlement_assignment_policy_v001.csv"

REFERENCE_POINTS_PATH = QUALIFIED_ROOT / "novegeo_place_reference_points_v001.csv"
FOOTPRINTS_PATH = QUALIFIED_ROOT / "novegeo_settlement_footprints_v001.geojson"
RELATIONSHIPS_PATH = RELATIONSHIP_ROOT / "novegeo_place_spatial_relationships_v001.csv"
ASSIGNMENTS_PATH = RELATIONSHIP_ROOT / "novegeo_effective_dated_place_geometry_assignments_v001.csv"
QUALIFICATION_RESULTS_PATH = EVIDENCE_ROOT / "novegeo_place_spatial_qualification_results_v001.csv"
SOURCE_HASHES_PATH = EVIDENCE_ROOT / "novegeo_place_spatialization_source_hashes_v001.csv"
SUMMARY_PATH = EVIDENCE_ROOT / "novegeo_place_spatialization_summary_v001.json"

BUNDLE_CODE = "P006.7.11.10"
BUNDLE_NAME = "Place Spatial Association and Settlement Geometry"
BUNDLE_VERSION = 1
BUNDLE_EFFECTIVE_DATE = "2026-08-22"
SOURCE_REPOSITORY_REVISION = "25b1f34db429632d409920631140e1265f8c84bf"
RUNTIME_MODE = "production"
EFFECT_SCOPE = "SHARED_REFERENCE"
CRS_CODE = "NG-CRS-EPSG4326"
PLACE_DATASET_ID = "dataset:novegeo:place-spatial-association"
PLACE_DATASET_VERSION = "1"
SOVEREIGN_BOUNDARY_ID = "boundary:novegeo:sovereign"
SOVEREIGN_BOUNDARY_VERSION = 2

EXPECTED_PLACE_TYPE_COUNTS = {
    "VILLAGE": 240,
    "TOWN": 120,
    "SUBURB": 96,
    "TOWNSHIP": 72,
    "CITY_DISTRICT": 64,
    "MARKET_CENTRE": 40,
    "MUNICIPALITY": 24,
    "INDUSTRIAL_ZONE": 16,
    "RESORT_SETTLEMENT": 12,
    "CITY": 8,
    "ISLAND_SETTLEMENT": 8,
}
EXPECTED_REGION_COUNTS = {
    "NGR-01": 85,
    "NGR-02": 87,
    "NGR-03": 85,
    "NGR-04": 88,
    "NGR-05": 86,
    "NGR-06": 86,
    "NGR-07": 91,
    "NGR-08": 92,
}


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))


def sha256_path(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(*parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return sha256(payload).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}{stable_hash(*parts)}"


def payload_sha256(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(data).hexdigest()


def deterministic_fraction(*parts: object) -> float:
    digest = stable_hash(*parts)
    return int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)


INPUT_PATHS = (
    SETTLEMENT_SITING_PATH,
    CANONICAL_ALIGNMENT_PATH,
    COORDINATE_CANDIDATES_PATH,
    CONTAINMENT_PATH,
    SPATIAL_CROSSWALK_PATH,
    ENVIRONMENT_BINDINGS_PATH,
    SOVEREIGN_VERTICES_PATH,
    SOVEREIGN_PARTS_PATH,
    SETTLEMENT_NAME_CATALOGUE_PATH,
    HYDROLOGY_PATH,
    WORLD_BOUNDARY_GEOJSON_PATH,
    REGION_ANCHOR_POLICY_PATH,
    SETTLEMENT_POLICY_PATH,
    ISLAND_POLICY_PATH,
)

__all__ = [
    name for name in globals()
    if name.isupper() or name in {"csv_rows", "sha256_path", "stable_hash", "stable_id", "payload_sha256", "deterministic_fraction"}
]
