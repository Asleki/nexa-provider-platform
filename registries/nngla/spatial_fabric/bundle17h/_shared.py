"""Bundle 17H source paths, hashing and CSV helpers."""
from __future__ import annotations

from csv import DictReader
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GRA_ROOT = ROOT / "data" / "novegeo" / "nngla" / "geometry-roads-addresses" / "source"
CONTROLLED_ROOT = GRA_ROOT / "02_controlled_codes"
ROADS_ADDRESSES_ROOT = GRA_ROOT / "06_roads_addresses"
RELATIONSHIPS_ROOT = GRA_ROOT / "08_relationships"
EVIDENCE_ROOT = GRA_ROOT / "10_evidence"
SPATIAL_ROOT = ROOT / "data" / "novegeo" / "nngla" / "spatial-fabric" / "source"
ALIGNMENT_PATH = SPATIAL_ROOT / "08_relationships" / "novegeo_existing_canonical_alignment_v002.csv"
ROAD_SOURCE_PATH = ROADS_ADDRESSES_ROOT / "road_reference_candidates.csv"
DAY_ZERO_ADDRESS_PATH = ROADS_ADDRESSES_ROOT / "address_reference_candidates.csv"
SETTLEMENT_CATALOGUE_PATH = ROOT / "data" / "novegeo" / "nngla" / "geographic-identity-places" / "source" / "04_name_catalogues" / "settlement_name_catalogue.csv"
HOUSE_CATALOGUE_SOURCE_NAME = "citizen_house_construction_catalogue.csv"
HOUSE_CATALOGUE_SHA256 = "0cf6c97286f62dc86414ae7aedb026a69faec4fb92a1b5dd85fd4fbb42273078"
GOVERNED_PLACES_DATASET_ID = "dataset:novegeo:places:v001:700"
LEGACY_PLACES_REFERENCE = "novegeo_places_registry_v001_700.csv"
RUNTIME_MODES = frozenset({"simulation", "production"})


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))


def csv_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = DictReader(handle)
        return tuple(reader.fieldnames or ())


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}{sha256(payload).hexdigest()}"


__all__ = [
    "ROOT", "GRA_ROOT", "CONTROLLED_ROOT", "ROADS_ADDRESSES_ROOT", "RELATIONSHIPS_ROOT", "EVIDENCE_ROOT",
    "SPATIAL_ROOT", "ALIGNMENT_PATH", "ROAD_SOURCE_PATH", "DAY_ZERO_ADDRESS_PATH", "SETTLEMENT_CATALOGUE_PATH",
    "HOUSE_CATALOGUE_SOURCE_NAME", "HOUSE_CATALOGUE_SHA256", "GOVERNED_PLACES_DATASET_ID", "LEGACY_PLACES_REFERENCE",
    "RUNTIME_MODES", "csv_rows", "csv_header", "stable_id",
]
