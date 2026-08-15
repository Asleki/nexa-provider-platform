"""P006.7.11.3 governed NNGLA migration source catalogue.

This module reads repository evidence only.  It performs no database access and
never promotes a reference catalogue row into a canonical physical object.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
import csv
import json
from collections.abc import Mapping


ROOT = Path(__file__).resolve().parents[3]


class SourceKind(str, Enum):
    CANONICAL_OBJECT_CANDIDATE = "CANONICAL_OBJECT_CANDIDATE"
    REFERENCE_CATALOGUE = "REFERENCE_CATALOGUE"
    SOVEREIGN_AUTHORITY = "SOVEREIGN_AUTHORITY"
    EMPTY_GOVERNED_REGISTER = "EMPTY_GOVERNED_REGISTER"


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    source_key: str
    kind: SourceKind
    relative_path: str
    source_id_field: str
    domain_family: str
    dataset_id: str
    dataset_version: str

    @property
    def path(self) -> Path:
        return ROOT / self.relative_path


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    row_number: int
    payload: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    descriptor: SourceDescriptor
    records: tuple[SourceRecord, ...]
    source_sha256: str
    byte_size: int

    @property
    def governed_empty(self) -> bool:
        return self.descriptor.kind is SourceKind.EMPTY_GOVERNED_REGISTER and not self.records


_BASE = "data/novegeo/nngla"
SOURCE_DESCRIPTORS: dict[str, SourceDescriptor] = {
    "places": SourceDescriptor(
        "places", SourceKind.CANONICAL_OBJECT_CANDIDATE,
        f"{_BASE}/geographic-identity-places/source/04_name_catalogues/settlement_name_catalogue.csv",
        "source_place_code", "PLACE", "dataset:novegeo:places:v001:700", "1",
    ),
    "administrative-areas": SourceDescriptor(
        "administrative-areas", SourceKind.CANONICAL_OBJECT_CANDIDATE,
        f"{_BASE}/geographic-identity-places/source/05_geographic_candidates/administrative_area_candidates.csv",
        "administrative_candidate_id", "ADMINISTRATIVE_AREA", "dataset:novegeo:administrative-areas:v001:192", "1",
    ),
    "geographic-features": SourceDescriptor(
        "geographic-features", SourceKind.CANONICAL_OBJECT_CANDIDATE,
        f"{_BASE}/geographic-identity-places/source/05_geographic_candidates/geographic_feature_candidates.csv",
        "feature_candidate_id", "GEOGRAPHIC_FEATURE", "dataset:novegeo:geographic-features:v001:21", "1",
    ),
    "geometry": SourceDescriptor(
        "geometry", SourceKind.CANONICAL_OBJECT_CANDIDATE,
        f"{_BASE}/geometry-roads-addresses/source/05_geographic_candidates/geometry_version_candidates.csv",
        "geometry_version_candidate_id", "GEOMETRY", "dataset:novegeo:geometry-versions:v001:21", "1",
    ),
    "survey-control": SourceDescriptor(
        "survey-control", SourceKind.EMPTY_GOVERNED_REGISTER,
        f"{_BASE}/geometry-roads-addresses/source/05_geographic_candidates/survey_control_point_candidates.csv",
        "survey_control_candidate_id", "SURVEY_CONTROL", "dataset:novegeo:survey-control:v001:empty", "1",
    ),
    "roads": SourceDescriptor(
        "roads", SourceKind.CANONICAL_OBJECT_CANDIDATE,
        f"{_BASE}/geometry-roads-addresses/source/06_roads_addresses/road_reference_candidates.csv",
        "road_candidate_id", "ROAD", "dataset:novegeo:roads:v001:900", "1",
    ),
    "addresses": SourceDescriptor(
        "addresses", SourceKind.EMPTY_GOVERNED_REGISTER,
        f"{_BASE}/geometry-roads-addresses/source/06_roads_addresses/address_reference_candidates.csv",
        "address_candidate_id", "ADDRESS", "dataset:novegeo:addresses:v001:empty", "1",
    ),
    "parcels": SourceDescriptor(
        "parcels", SourceKind.EMPTY_GOVERNED_REGISTER,
        f"{_BASE}/cadastre-titles-state-land/source/07_land/parcel_bootstrap.csv",
        "parcel_id", "PARCEL", "dataset:novegeo:parcels:v001:empty", "1",
    ),
    "titles": SourceDescriptor(
        "titles", SourceKind.EMPTY_GOVERNED_REGISTER,
        f"{_BASE}/cadastre-titles-state-land/source/07_land/title_bootstrap.csv",
        "title_id", "TITLE", "dataset:novegeo:titles:v001:empty", "1",
    ),
    "state-land": SourceDescriptor(
        "state-land", SourceKind.EMPTY_GOVERNED_REGISTER,
        f"{_BASE}/cadastre-titles-state-land/source/07_land/state_land_bootstrap.csv",
        "state_land_record_id", "STATE_LAND", "dataset:novegeo:state-land:v001:empty", "1",
    ),
    "sovereign-boundary": SourceDescriptor(
        "sovereign-boundary", SourceKind.SOVEREIGN_AUTHORITY,
        "data/novegeo/geography/world-boundary/candidate/novegeo_world_boundary_v002.geojson",
        "boundaryId", "SOVEREIGN_BOUNDARY", "dataset:novegeo:world-boundary", "2",
    ),
}

_NAME_FAMILIES = (
    "hill", "valley", "river", "forest", "mountain", "lake", "bay", "cape",
    "island", "plain", "plateau", "wetland", "road", "settlement",
    "administrative", "bridge", "landmark", "square",
)
for family in _NAME_FAMILIES:
    SOURCE_DESCRIPTORS[f"names:{family}"] = SourceDescriptor(
        f"names:{family}", SourceKind.REFERENCE_CATALOGUE,
        f"{_BASE}/geographic-identity-places/source/04_name_catalogues/{family}_name_catalogue.csv",
        "", f"GEOGRAPHIC_NAME:{family.upper()}", f"dataset:novegeo:name-catalogue:{family}:v001", "1",
    )


def _csv_records(descriptor: SourceDescriptor) -> tuple[SourceRecord, ...]:
    with descriptor.path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    records: list[SourceRecord] = []
    for index, row in enumerate(rows, start=2):
        field = descriptor.source_id_field
        source_id = str(row.get(field, "")).strip() if field else ""
        if not source_id:
            # Reference catalogues intentionally have family-specific ID columns.
            id_candidates = [key for key in row if key.endswith("_name_record_id") or key in {"name_id", "record_id"}]
            if len(id_candidates) != 1:
                raise ValueError(f"cannot determine source ID for {descriptor.source_key} row {index}")
            source_id = str(row[id_candidates[0]]).strip()
        records.append(SourceRecord(source_id, index, dict(row)))
    return tuple(records)


def _geojson_records(descriptor: SourceDescriptor) -> tuple[SourceRecord, ...]:
    payload = json.loads(descriptor.path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    records: list[SourceRecord] = []
    for index, feature in enumerate(features, start=1):
        properties = dict(feature.get("properties") or {})
        source_id = str(properties.get(descriptor.source_id_field, "")).strip()
        if not source_id:
            raise ValueError(f"missing {descriptor.source_id_field} in {descriptor.relative_path}")
        serializable = {key: str(value) if value is not None else "" for key, value in properties.items()}
        serializable["geometry_type"] = str((feature.get("geometry") or {}).get("type", ""))
        records.append(SourceRecord(source_id, index, serializable))
    return tuple(records)


def load_source(source_key: str) -> SourceSnapshot:
    try:
        descriptor = SOURCE_DESCRIPTORS[source_key]
    except KeyError as exc:
        raise KeyError(f"unknown governed NNGLA migration source: {source_key}") from exc
    raw = descriptor.path.read_bytes()
    if descriptor.path.suffix.lower() == ".csv":
        records = _csv_records(descriptor)
    elif descriptor.path.suffix.lower() in {".json", ".geojson"}:
        records = _geojson_records(descriptor)
    else:
        raise ValueError(f"unsupported governed source type: {descriptor.path.suffix}")
    if descriptor.kind is SourceKind.EMPTY_GOVERNED_REGISTER and records:
        raise ValueError(f"governed empty register unexpectedly contains records: {source_key}")
    return SourceSnapshot(descriptor, records, sha256(raw).hexdigest(), len(raw))


__all__ = [
    "ROOT",
    "SourceKind",
    "SourceDescriptor",
    "SourceRecord",
    "SourceSnapshot",
    "SOURCE_DESCRIPTORS",
    "load_source",
]
