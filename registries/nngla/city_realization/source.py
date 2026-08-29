"""Locked Bundle19B CITY evidence reader for P006.7.11.15.8.

Bundle19B is provenance/coordinate evidence only.  Loading a feature here does
not make it authoritative; authority is created only by the governed writer into
P006.7.11.15.7's CITY tables.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .contracts import (
    CitySourceEvidence,
    CRS_CODE,
    OFFICIAL_CITY_SET,
    OFFICIAL_NOVEGEO_CITY_IDS,
    RUNTIME_EFFECT_SCOPE,
)

ROOT = Path(__file__).resolve().parents[3]
BUNDLE19B_BOUNDARIES = (
    ROOT
    / "data"
    / "novegeo"
    / "nngla"
    / "spatial-fabric"
    / "bundle19b"
    / "qualified"
    / "novegeo_administrative_boundaries_v001.geojson"
)
SOURCE_PATH_REFERENCE = BUNDLE19B_BOUNDARIES.relative_to(ROOT).as_posix()
EXPECTED_DATASET_ID = "dataset:novegeo:administrative-boundaries"
EXPECTED_DATASET_VERSION = "1"
EXPECTED_FEATURE_COUNT = 192


def canonical_json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _read_payload(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("Bundle19B boundary artifact must be a JSON object")
    return payload, sha256(raw).hexdigest()


def _normalize_version(value: object) -> str:
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


def load_city_sources(path: Path | None = None) -> tuple[CitySourceEvidence, ...]:
    artifact = Path(path or BUNDLE19B_BOUNDARIES)
    payload, dataset_sha = _read_payload(artifact)
    metadata = payload.get("metadata")
    features = payload.get("features")
    if not isinstance(metadata, dict) or not isinstance(features, list):
        raise ValueError("Bundle19B boundary artifact is malformed")
    if metadata.get("dataset_id") != EXPECTED_DATASET_ID:
        raise ValueError("Bundle19B dataset identity changed")
    if _normalize_version(metadata.get("dataset_version")) != EXPECTED_DATASET_VERSION:
        raise ValueError("Bundle19B dataset version changed")
    if int(metadata.get("feature_count", -1)) != EXPECTED_FEATURE_COUNT or len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Bundle19B requires exactly 192 administrative boundary features")
    if metadata.get("crs_code") != CRS_CODE:
        raise ValueError("Bundle19B CRS contract changed")
    if metadata.get("runtime_effect_scope") != RUNTIME_EFFECT_SCOPE:
        raise ValueError("Bundle19B runtime effect scope changed")

    source_path_reference = (
        artifact.relative_to(ROOT).as_posix()
        if artifact.is_relative_to(ROOT)
        else artifact.as_posix()
    )
    out: list[CitySourceEvidence] = []
    seen: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("Bundle19B feature must be a JSON object")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise ValueError("Bundle19B feature properties/geometry are required")
        if str(properties.get("administrative_type_code", "")).upper() != "CITY":
            continue
        city_id = str(properties.get("administrative_area_id", ""))
        if city_id not in OFFICIAL_CITY_SET:
            raise ValueError(f"Bundle19B exposed unexpected CITY identity: {city_id}")
        if city_id in seen:
            raise ValueError(f"Bundle19B duplicated CITY identity: {city_id}")
        seen.add(city_id)
        geometry_type = str(properties.get("geometry_type_code", "")).upper()
        if geometry_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise ValueError(f"CITY source geometry is not polygonal: {city_id}")
        expected_geojson_type = "MultiPolygon" if geometry_type == "MULTIPOLYGON" else "Polygon"
        if geometry.get("type") != expected_geojson_type:
            raise ValueError(f"CITY source geometry metadata mismatch: {city_id}")
        if properties.get("crs_code") != CRS_CODE:
            raise ValueError(f"CITY source CRS mismatch: {city_id}")
        if properties.get("runtime_effect_scope") != RUNTIME_EFFECT_SCOPE:
            raise ValueError(f"CITY source runtime scope mismatch: {city_id}")
        if properties.get("qualification_status") != "QUALIFIED":
            raise ValueError(f"CITY source is not qualified: {city_id}")
        if properties.get("legalization_status") != "APPROVED_FOR_GOVERNED_LIVE_APPLICATION":
            raise ValueError(f"CITY source is not approved for governed live application: {city_id}")
        out.append(
            CitySourceEvidence(
                administrative_area_id=city_id,
                canonical_name=str(properties.get("canonical_name", "")).strip(),
                region_code=str(properties.get("region_code", "")).strip(),
                source_record_id=str(properties.get("source_record_id", "")).strip(),
                boundary_candidate_id=str(properties.get("boundary_candidate_id", "")).strip(),
                source_dataset_id=EXPECTED_DATASET_ID,
                source_dataset_version=EXPECTED_DATASET_VERSION,
                source_path_reference=source_path_reference,
                source_dataset_sha256=dataset_sha,
                source_geometry_sha256=canonical_json_sha256(geometry),
                geometry_type_code=geometry_type,
                geometry=geometry,
            )
        )
    ordered = tuple(sorted(out, key=lambda item: item.administrative_area_id))
    if tuple(item.administrative_area_id for item in ordered) != OFFICIAL_NOVEGEO_CITY_IDS:
        raise ValueError("Bundle19B official CITY set changed")
    if any(not item.canonical_name or not item.region_code or not item.source_record_id for item in ordered):
        raise ValueError("Bundle19B CITY provenance fields are incomplete")
    return ordered


def load_city_source(city_id: str) -> CitySourceEvidence:
    normalized = str(city_id).strip()
    if normalized not in OFFICIAL_CITY_SET:
        raise ValueError(f"unsupported official NoveGeo CITY identity: {normalized}")
    for item in load_city_sources():
        if item.administrative_area_id == normalized:
            return item
    raise RuntimeError(f"official CITY source evidence missing: {normalized}")
