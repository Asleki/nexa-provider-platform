"""Bundle19A multi-artifact TOWN source reader.

Authority is intentionally split across the evidence summary, the qualified place-reference
CSV, and the qualified settlement-footprint GeoJSON. No metadata is invented inside the
GeoJSON and no legal-boundary meaning is inferred from a settlement footprint.
"""
from __future__ import annotations

from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

from .contracts import (
    CRS_CODE,
    EXPECTED_PARENT_COUNT,
    EXPECTED_PER_PARENT,
    EXPECTED_SETTLEMENT_FOOTPRINT_COUNT,
    EXPECTED_TOWN_COUNT,
    FOOTPRINT_SHA256,
    GEOMETRY_ROLE_CODE,
    LEGAL_BOUNDARY_STATUS,
    REFERENCE_SHA256,
    RUNTIME_EFFECT_SCOPE,
    SOURCE_BASIS,
    SOURCE_DATASET_ID,
    SOURCE_DATASET_VERSION,
    SOURCE_QUALIFICATION_STATUS,
    TownSourceEvidence,
)
from .planning import canonical_sha256

_PLACE_ID = re.compile(r"^NG-PLC-[0-9]{6}$")


def _sha(path: Path) -> tuple[bytes, str]:
    raw = Path(path).read_bytes()
    return raw, sha256(raw).hexdigest()


def load_town_sources(
    footprint_path: Path,
    reference_path: Path,
    summary_path: Path,
) -> tuple[TownSourceEvidence, ...]:
    footprint_path = Path(footprint_path)
    reference_path = Path(reference_path)
    summary_path = Path(summary_path)

    footprint_raw, footprint_sha = _sha(footprint_path)
    reference_raw, reference_sha = _sha(reference_path)
    summary_raw, summary_sha = _sha(summary_path)
    if footprint_sha != FOOTPRINT_SHA256:
        raise ValueError("Bundle19A settlement-footprint SHA-256 changed")
    if reference_sha != REFERENCE_SHA256:
        raise ValueError("Bundle19A place-reference SHA-256 changed")

    summary = json.loads(summary_raw.decode("utf-8-sig"))
    if summary.get("source_dataset_id") != SOURCE_DATASET_ID:
        raise ValueError("Bundle19A source dataset identity changed")
    if str(summary.get("source_dataset_version")) != SOURCE_DATASET_VERSION:
        raise ValueError("Bundle19A source dataset version changed")
    if summary.get("runtime_effect_scope") != RUNTIME_EFFECT_SCOPE:
        raise ValueError("Bundle19A runtime-effect scope changed")
    if str(summary.get("qualification_status", "")).upper() != "PASS":
        raise ValueError("Bundle19A source bundle is not PASS")
    if int((summary.get("counts") or {}).get("settlement_footprints", -1)) != EXPECTED_SETTLEMENT_FOOTPRINT_COUNT:
        raise ValueError("Bundle19A settlement-footprint count changed")

    with reference_path.open(encoding="utf-8-sig", newline="") as handle:
        references = list(csv.DictReader(handle))
    if len(references) != 700:
        raise ValueError("Bundle19A place-reference count changed")
    ref_by_place = {str(row.get("place_id", "")): row for row in references}
    ref_by_source = {str(row.get("source_place_code", "")): row for row in references}
    if len(ref_by_place) != 700 or len(ref_by_source) != 700:
        raise ValueError("Bundle19A place-reference identities are not unique")

    payload = json.loads(footprint_raw.decode("utf-8-sig"))
    features = payload.get("features")
    if not isinstance(features, list) or len(features) != EXPECTED_SETTLEMENT_FOOTPRINT_COUNT:
        raise ValueError("Bundle19A settlement-footprint artifact count changed")

    source_set_sha = canonical_sha256(
        {
            "datasetId": SOURCE_DATASET_ID,
            "datasetVersion": SOURCE_DATASET_VERSION,
            "summarySha256": summary_sha,
            "referenceSha256": reference_sha,
            "footprintSha256": footprint_sha,
        }
    )
    source_paths = "|".join(
        (summary_path.as_posix(), reference_path.as_posix(), footprint_path.as_posix())
    )

    output: list[TownSourceEvidence] = []
    seen: set[str] = set()
    parent_counts: Counter[str] = Counter()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("Bundle19A settlement-footprint feature must be an object")
        props = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            raise ValueError("Bundle19A settlement-footprint properties/geometry are required")
        if str(props.get("place_type_code", "")).upper() != "TOWN":
            continue

        place_id = str(props.get("place_id", "")).strip()
        if not _PLACE_ID.fullmatch(place_id) or place_id in seen:
            raise ValueError(f"invalid/duplicate TOWN place identity: {place_id}")
        reference = ref_by_place.get(place_id)
        if reference is None:
            raise ValueError(f"TOWN has no qualified place-reference row: {place_id}")
        parent_source = str(reference.get("parent_source_place_code", "")).strip()
        parent_reference = ref_by_source.get(parent_source)
        if not parent_source or parent_reference is None:
            raise ValueError(f"TOWN parent reference is unavailable: {place_id}")
        if str(parent_reference.get("place_type_code", "")).upper() != "MUNICIPALITY":
            raise ValueError(f"TOWN parent is not MUNICIPALITY: {place_id}")

        pairs = (
            ("source_place_code", props.get("source_place_code"), reference.get("source_place_code")),
            ("canonical_name", props.get("canonical_name"), reference.get("canonical_name")),
            ("place_type_code", str(props.get("place_type_code", "")).upper(), str(reference.get("place_type_code", "")).upper()),
            ("region_code", props.get("region_code"), reference.get("region_code")),
        )
        for field, left, right in pairs:
            if str(left or "") != str(right or ""):
                raise ValueError(f"TOWN cross-artifact {field} mismatch: {place_id}")

        geometry_type = str(geometry.get("type", "")).upper()
        if geometry_type != "POLYGON":
            raise ValueError(f"TOWN settlement footprint must remain Polygon: {place_id}")
        if str(props.get("crs_code", "")) != CRS_CODE:
            raise ValueError(f"TOWN footprint CRS changed: {place_id}")
        if str(props.get("runtime_effect_scope", "")) != RUNTIME_EFFECT_SCOPE:
            raise ValueError(f"TOWN runtime-effect scope changed: {place_id}")
        if str(props.get("geometry_role_code", "")) != GEOMETRY_ROLE_CODE:
            raise ValueError(f"TOWN geometry role changed: {place_id}")
        if str(props.get("qualification_status", "")) != SOURCE_QUALIFICATION_STATUS:
            raise ValueError(f"TOWN source qualification status changed: {place_id}")
        if str(props.get("legal_boundary_status", "")) != LEGAL_BOUNDARY_STATUS:
            raise ValueError(f"TOWN legal-boundary status changed: {place_id}")
        if str(props.get("source_basis", "")) != SOURCE_BASIS:
            raise ValueError(f"TOWN source basis changed: {place_id}")

        seen.add(place_id)
        parent_counts[parent_source] += 1
        output.append(
            TownSourceEvidence(
                place_id=place_id,
                canonical_name=str(props["canonical_name"]),
                region_code=str(props["region_code"]),
                source_place_code=str(props["source_place_code"]),
                parent_source_place_code=parent_source,
                geometry_role_code=GEOMETRY_ROLE_CODE,
                legal_boundary_status=LEGAL_BOUNDARY_STATUS,
                qualification_status=SOURCE_QUALIFICATION_STATUS,
                source_basis=SOURCE_BASIS,
                dataset_id=SOURCE_DATASET_ID,
                dataset_version=SOURCE_DATASET_VERSION,
                runtime_effect_scope=RUNTIME_EFFECT_SCOPE,
                source_path_reference=source_paths,
                source_dataset_sha256=source_set_sha,
                source_reference_sha256=reference_sha,
                source_footprint_sha256=footprint_sha,
                source_geometry_sha256=canonical_sha256(geometry),
                geometry_type_code=geometry_type,
                geometry=geometry,
            )
        )

    if len(output) != EXPECTED_TOWN_COUNT:
        raise ValueError("Bundle19A TOWN count changed")
    if len(parent_counts) != EXPECTED_PARENT_COUNT or set(parent_counts.values()) != {EXPECTED_PER_PARENT}:
        raise ValueError("Bundle19A TOWN parent grouping changed")
    return tuple(sorted(output, key=lambda row: row.place_id))
