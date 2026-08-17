"""Bundle 17F source-path and deterministic CSV helpers."""
from __future__ import annotations
from csv import DictReader
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NNGLA_ROOT = ROOT / "data" / "novegeo" / "nngla"
SPATIAL_ROOT = NNGLA_ROOT / "spatial-fabric" / "source"
PLACE_PATH = NNGLA_ROOT / "geographic-identity-places" / "source" / "04_name_catalogues" / "settlement_name_catalogue.csv"
ADMIN_PATH = NNGLA_ROOT / "geographic-identity-places" / "source" / "05_geographic_candidates" / "administrative_area_candidates.csv"
FEATURE_PATH = NNGLA_ROOT / "geographic-identity-places" / "source" / "05_geographic_candidates" / "geographic_feature_candidates.csv"
GEOMETRY_PATH = NNGLA_ROOT / "geometry-roads-addresses" / "source" / "05_geographic_candidates" / "geometry_version_candidates.csv"
ROAD_PATH = NNGLA_ROOT / "geometry-roads-addresses" / "source" / "06_roads_addresses" / "road_reference_candidates.csv"
SETTLEMENT_SITING_PATH = SPATIAL_ROOT / "04_settlements_roads_administration" / "novegeo_settlement_siting_candidates_v001.csv"
ROAD_ALIGNMENT_PATH = SPATIAL_ROOT / "04_settlements_roads_administration" / "novegeo_road_alignment_candidates_v001.csv"
ADMIN_BOUNDARY_PATH = SPATIAL_ROOT / "04_settlements_roads_administration" / "novegeo_administrative_boundary_candidates_v001.csv"

LOCKED_CANONICAL_COUNTS = {
    "PLACE": 700,
    "ADMINISTRATIVE_AREA": 192,
    "ROAD": 350,
    "GEOGRAPHIC_FEATURE": 21,
    "EXISTING_GEOMETRY": 21,
}


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def governed_suffix(value: str) -> str:
    suffix = str(value).rsplit("-", 1)[-1]
    if not suffix.isdigit() or len(suffix) != 6:
        raise ValueError(f"governed six-digit suffix required: {value!r}")
    return suffix


__all__ = [
    "ROOT", "NNGLA_ROOT", "SPATIAL_ROOT", "PLACE_PATH", "ADMIN_PATH", "FEATURE_PATH", "GEOMETRY_PATH",
    "ROAD_PATH", "SETTLEMENT_SITING_PATH", "ROAD_ALIGNMENT_PATH", "ADMIN_BOUNDARY_PATH",
    "LOCKED_CANONICAL_COUNTS", "csv_rows", "file_sha256", "governed_suffix",
]
