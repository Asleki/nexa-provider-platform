"""Locked Bundle19B CITY_DISTRICT source reader."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from .contracts import (
    CRS_CODE,
    EXPECTED_CITY_DISTRICT_COUNT,
    EXPECTED_PER_CITY,
    RUNTIME_EFFECT_SCOPE,
    SOURCE_DATASET_ID,
    SOURCE_DATASET_SHA256,
    SOURCE_DATASET_VERSION,
    CityDistrictSourceEvidence,
)
from .planning import canonical_sha256

_ADMIN_ID = re.compile(r"^NG-ADM-[0-9]{6}$")


def load_city_district_sources(path: Path) -> tuple[CityDistrictSourceEvidence, ...]:
    artifact = Path(path)
    raw = artifact.read_bytes()
    actual_sha = sha256(raw).hexdigest()
    if actual_sha != SOURCE_DATASET_SHA256:
        raise ValueError("Bundle19B administrative-boundary artifact SHA-256 changed")

    payload = json.loads(raw.decode("utf-8-sig"))
    metadata = payload.get("metadata")
    features = payload.get("features")
    if not isinstance(metadata, dict) or not isinstance(features, list):
        raise ValueError("Bundle19B administrative-boundary artifact is malformed")

    if metadata.get("dataset_id") != SOURCE_DATASET_ID:
        raise ValueError("Bundle19B dataset identity changed")
    if str(metadata.get("dataset_version")).removesuffix(".0") != SOURCE_DATASET_VERSION:
        raise ValueError("Bundle19B dataset version changed")
    if int(metadata.get("feature_count", -1)) != 192 or len(features) != 192:
        raise ValueError("Bundle19B feature count changed")
    if metadata.get("crs_code") != CRS_CODE:
        raise ValueError("Bundle19B CRS changed")
    if metadata.get("runtime_effect_scope") != RUNTIME_EFFECT_SCOPE:
        raise ValueError("Bundle19B runtime-effect scope changed")

    rows: list[CityDistrictSourceEvidence] = []
    seen: set[str] = set()
    parent_counts: Counter[str] = Counter()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("Bundle19B feature must be an object")
        props = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            raise ValueError("Bundle19B feature properties/geometry are required")
        if str(props.get("administrative_type_code", "")).upper() != "CITY_DISTRICT":
            continue

        district_id = str(props.get("administrative_area_id", "")).strip()
        parent_source_record_id = str(props.get("parent_source_record_id", "")).strip()
        if not _ADMIN_ID.fullmatch(district_id) or district_id in seen:
            raise ValueError(f"invalid/duplicate CITY_DISTRICT identity: {district_id}")
        if not parent_source_record_id:
            raise ValueError(f"CITY_DISTRICT parent source record missing: {district_id}")
        if str(props.get("qualification_status", "")).upper() != "QUALIFIED":
            raise ValueError(f"CITY_DISTRICT source is not QUALIFIED: {district_id}")
        geometry_type = str(props.get("geometry_type_code", geometry.get("type", ""))).upper()
        if geometry_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise ValueError(f"CITY_DISTRICT source geometry is not polygonal: {district_id}")

        canonical_name = str(props.get("canonical_name", "")).strip()
        region_code = str(props.get("region_code", "")).strip()
        source_record_id = str(props.get("source_record_id", "")).strip()
        if not canonical_name or not region_code or not source_record_id:
            raise ValueError(f"CITY_DISTRICT identity/provenance incomplete: {district_id}")

        seen.add(district_id)
        parent_counts[parent_source_record_id] += 1
        rows.append(
            CityDistrictSourceEvidence(
                administrative_area_id=district_id,
                canonical_name=canonical_name,
                region_code=region_code,
                source_record_id=source_record_id,
                parent_source_record_id=parent_source_record_id,
                source_dataset_id=SOURCE_DATASET_ID,
                source_dataset_version=SOURCE_DATASET_VERSION,
                source_path_reference=artifact.as_posix(),
                source_dataset_sha256=actual_sha,
                source_geometry_sha256=canonical_sha256(geometry),
                geometry_type_code=geometry_type,
                geometry=geometry,
            )
        )

    if len(rows) != EXPECTED_CITY_DISTRICT_COUNT:
        raise ValueError("Bundle19B CITY_DISTRICT count changed")
    if len(parent_counts) != 8 or set(parent_counts.values()) != {EXPECTED_PER_CITY}:
        raise ValueError("Bundle19B CITY_DISTRICT parent grouping changed")
    return tuple(sorted(rows, key=lambda row: row.administrative_area_id))


def sources_for_city_source_record(
    path: Path,
    city_source_record_id: str,
) -> tuple[CityDistrictSourceEvidence, ...]:
    selected = tuple(
        row
        for row in load_city_district_sources(path)
        if row.parent_source_record_id == str(city_source_record_id).strip()
    )
    if len(selected) != EXPECTED_PER_CITY:
        raise ValueError("exactly eight CITY_DISTRICT sources are required per CITY")
    return selected
