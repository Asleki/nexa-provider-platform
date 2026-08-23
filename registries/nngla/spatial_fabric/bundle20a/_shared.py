"""Shared paths and deterministic helpers for P006.7.11.12 / Bundle 20A."""
from __future__ import annotations
from csv import DictReader
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[4]
SPATIAL_ROOT = ROOT / "data" / "novegeo" / "nngla" / "spatial-fabric"
BUNDLE_ROOT = SPATIAL_ROOT / "bundle20a"
CONTROL_ROOT = BUNDLE_ROOT / "controlled"
QUALIFIED_ROOT = BUNDLE_ROOT / "qualified"
RELATIONSHIP_ROOT = BUNDLE_ROOT / "relationships"
EVIDENCE_ROOT = BUNDLE_ROOT / "evidence"

ROAD_SOURCE = ROOT / "data" / "novegeo" / "nngla" / "geometry-roads-addresses" / "source" / "06_roads_addresses" / "road_reference_candidates.csv"
CANONICAL_ALIGNMENT = SPATIAL_ROOT / "source" / "08_relationships" / "novegeo_existing_canonical_alignment_v002.csv"
PLACE_POINTS = SPATIAL_ROOT / "bundle19a" / "qualified" / "novegeo_place_reference_points_v001.csv"
ADMIN_BOUNDARIES = SPATIAL_ROOT / "bundle19b" / "qualified" / "novegeo_administrative_boundaries_v001.geojson"
HYDROLOGY = ROOT / "data" / "novegeo" / "geography" / "hydrology" / "qualified" / "novegeo_hydrology_v001.json"
WORLD_BOUNDARY = ROOT / "data" / "novegeo" / "geography" / "world-boundary" / "candidate" / "novegeo_world_boundary_v002.geojson"

ROAD_POLICY = CONTROL_ROOT / "novegeo_road_network_authoring_policy_v001.csv"
ROAD_ALIGNMENT_PLAN = CONTROL_ROOT / "novegeo_road_alignment_plan_v001.csv"
ROAD_GEOMETRIES = QUALIFIED_ROOT / "novegeo_road_alignments_v001.geojson"
ROAD_SEGMENTS = QUALIFIED_ROOT / "novegeo_road_segments_v001.csv"
NETWORK_NODES = QUALIFIED_ROOT / "novegeo_road_network_nodes_v001.csv"
CONNECTIVITY = RELATIONSHIP_ROOT / "novegeo_road_network_connectivity_v001.csv"
ROAD_RELATIONSHIPS = RELATIONSHIP_ROOT / "novegeo_road_spatial_relationships_v001.csv"
ASSIGNMENTS = RELATIONSHIP_ROOT / "novegeo_effective_dated_road_geometry_assignments_v001.csv"
QUALIFICATION = EVIDENCE_ROOT / "novegeo_road_network_qualification_results_v001.csv"
SOURCE_HASHES = EVIDENCE_ROOT / "novegeo_road_network_source_hashes_v001.csv"
SUMMARY = EVIDENCE_ROOT / "novegeo_road_network_summary_v001.json"

BUNDLE_CODE = "P006.7.11.12"
BUNDLE_NAME = "Road Geometry and National Network Construction"
BUNDLE_VERSION = 1
BUNDLE_EFFECTIVE_DATE = "2026-08-23"
RUNTIME_MODE = "production"
EFFECT_SCOPE = "SHARED_REFERENCE"
CRS_CODE = "NG-CRS-EPSG4326"
GEOMETRY_ROLE = "ROAD_ALIGNMENT"
EXPECTED_ROAD_COUNT = 350
EXPECTED_CLASS_COUNTS = {k: 50 for k in ("ACCESS", "DISTRICT", "LOCAL", "MUNICIPAL", "REGIONAL", "RURAL", "SERVICE")}


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))


def json_payload(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_path(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def stable_hash(*parts: object) -> str:
    return sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    return prefix + stable_hash(*parts)


def road_id_from_candidate(candidate_id: str) -> str:
    return "NG-RD-" + candidate_id.rsplit("-", 1)[-1]


def haversine_m(coords: tuple[tuple[float, float], ...]) -> float:
    from math import asin, cos, radians, sin, sqrt
    total = 0.0
    radius = 6371008.8
    for (lon1, lat1), (lon2, lat2) in zip(coords, coords[1:]):
        p1, p2 = radians(lat1), radians(lat2)
        dp, dl = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dp/2)**2 + cos(p1)*cos(p2)*sin(dl/2)**2
        total += 2 * radius * asin(min(1.0, sqrt(a)))
    return total

INPUT_PATHS = (ROAD_SOURCE, CANONICAL_ALIGNMENT, PLACE_POINTS, ADMIN_BOUNDARIES, HYDROLOGY, WORLD_BOUNDARY, ROAD_POLICY, ROAD_ALIGNMENT_PLAN)
