"""Frozen Bundle19B MUNICIPALITY evidence reader.

Bundle19B is coordinate/identity/topology/provenance evidence only.  It is not
publication authority and is never a runtime map fallback.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from .contracts import (
    CRS_CODE,
    EXPECTED_MUNICIPALITY_COUNT,
    EXPECTED_PER_REGION,
    MunicipalitySourceEvidence,
    RUNTIME_EFFECT_SCOPE,
)
from .planning import canonical_sha256

ROOT = Path(__file__).resolve().parents[3]
BUNDLE19B_BOUNDARIES = (
    ROOT
    / "data/novegeo/nngla/spatial-fabric/bundle19b/qualified/"
      "novegeo_administrative_boundaries_v001.geojson"
)
EXPECTED_DATASET_ID = "dataset:novegeo:administrative-boundaries"
EXPECTED_DATASET_VERSION = "1"
EXPECTED_FEATURE_COUNT = 192
_ADMIN_ID = re.compile(r"^NG-ADM-[0-9]{6}$")


def load_municipality_sources(
    path: Path | None = None,
) -> tuple[MunicipalitySourceEvidence, ...]:
    artifact = Path(path or BUNDLE19B_BOUNDARIES)
    raw = artifact.read_bytes()
    payload = json.loads(raw.decode("utf-8-sig"))
    metadata = payload.get("metadata")
    features = payload.get("features")
    if not isinstance(metadata, dict) or not isinstance(features, list):
        raise ValueError("Bundle19B administrative boundary artifact is malformed")

    version = str(metadata.get("dataset_version", "")).strip()
    if version.endswith(".0"):
        version = version[:-2]
    if metadata.get("dataset_id") != EXPECTED_DATASET_ID:
        raise ValueError("Bundle19B dataset identity changed")
    if version != EXPECTED_DATASET_VERSION:
        raise ValueError("Bundle19B dataset version changed")
    if int(metadata.get("feature_count", -1)) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Bundle19B metadata feature_count changed")
    if len(features) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Bundle19B requires exactly 192 administrative boundary features")
    if metadata.get("crs_code") != CRS_CODE:
        raise ValueError("Bundle19B CRS contract changed")
    if metadata.get("runtime_effect_scope") != RUNTIME_EFFECT_SCOPE:
        raise ValueError("Bundle19B runtime-effect contract changed")

    dataset_sha = sha256(raw).hexdigest()
    try:
        source_path = artifact.relative_to(ROOT).as_posix()
    except ValueError:
        source_path = artifact.as_posix()

    rows: list[MunicipalitySourceEvidence] = []
    seen: set[str] = set()
    for feature in features:
        props = feature.get("properties") if isinstance(feature, dict) else None
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            raise ValueError("Bundle19B feature properties/geometry are required")
        if str(props.get("administrative_type_code", "")).upper() != "MUNICIPALITY":
            continue

        municipality_id = str(props.get("administrative_area_id", ""))
        if not _ADMIN_ID.fullmatch(municipality_id) or municipality_id in seen:
            raise ValueError(f"invalid or duplicate MUNICIPALITY identity: {municipality_id}")
        seen.add(municipality_id)

        geometry_type = str(props.get("geometry_type_code", "")).upper()
        expected_geojson = "MultiPolygon" if geometry_type == "MULTIPOLYGON" else "Polygon"
        if geometry_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise ValueError(f"invalid MUNICIPALITY source geometry type: {municipality_id}")
        if geometry.get("type") != expected_geojson:
            raise ValueError(f"MUNICIPALITY geometry metadata mismatch: {municipality_id}")
        if props.get("qualification_status") != "QUALIFIED":
            raise ValueError(f"MUNICIPALITY source is not qualified: {municipality_id}")
        if props.get("legalization_status") != "APPROVED_FOR_GOVERNED_LIVE_APPLICATION":
            raise ValueError(f"MUNICIPALITY source is not approved for governed live use: {municipality_id}")
        if props.get("crs_code") != CRS_CODE:
            raise ValueError(f"MUNICIPALITY source CRS changed: {municipality_id}")
        if props.get("runtime_effect_scope") != RUNTIME_EFFECT_SCOPE:
            raise ValueError(f"MUNICIPALITY source runtime-effect changed: {municipality_id}")

        rows.append(
            MunicipalitySourceEvidence(
                administrative_area_id=municipality_id,
                canonical_name=str(props.get("canonical_name", "")).strip(),
                region_code=str(props.get("region_code", "")).strip(),
                source_record_id=str(props.get("source_record_id", "")).strip(),
                parent_source_record_id=str(props.get("parent_source_record_id", "")).strip(),
                boundary_candidate_id=str(props.get("boundary_candidate_id", "")).strip(),
                source_dataset_id=EXPECTED_DATASET_ID,
                source_dataset_version=EXPECTED_DATASET_VERSION,
                source_path_reference=source_path,
                source_dataset_sha256=dataset_sha,
                source_geometry_sha256=canonical_sha256(geometry),
                geometry_type_code=geometry_type,
                geometry=geometry,
            )
        )

    ordered = tuple(sorted(rows, key=lambda row: row.administrative_area_id))
    counts = Counter(row.region_code for row in ordered)
    if len(ordered) != EXPECTED_MUNICIPALITY_COUNT:
        raise ValueError("Bundle19B requires exactly 24 MUNICIPALITY features")
    if len(counts) != 8 or any(count != EXPECTED_PER_REGION for count in counts.values()):
        raise ValueError("Bundle19B requires exactly three MUNICIPALITY features per REGION")
    if any(
        not row.canonical_name
        or not row.region_code
        or not row.source_record_id
        or not row.parent_source_record_id
        or not row.boundary_candidate_id
        for row in ordered
    ):
        raise ValueError("Bundle19B MUNICIPALITY identity/provenance fields are incomplete")
    return ordered


def sources_for_region_source_record(
    parent_source_record_id: str,
) -> tuple[MunicipalitySourceEvidence, ...]:
    rows = tuple(
        row
        for row in load_municipality_sources()
        if row.parent_source_record_id == str(parent_source_record_id)
    )
    if len(rows) != EXPECTED_PER_REGION:
        raise ValueError("exactly three MUNICIPALITY source features are required per REGION")
    return rows
