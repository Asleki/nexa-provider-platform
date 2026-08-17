"""Canonical POINT geometry allocation and effective-dated assignment for Bundle 17E."""
from __future__ import annotations

from functools import lru_cache

from ._shared import (
    BUNDLE_EFFECTIVE_DATE,
    COORDINATE_CANDIDATES_PATH,
    EFFECT_SCOPE,
    GEOMETRY_VERSION_CANDIDATES_PATH,
    csv_rows,
    payload_sha256,
    sequence_from_id,
    sha256_path,
    stable_id,
)
from .canonical import canonical_by_candidate, coordinate_candidate_rows, derive_spatial_canonical_crosswalk
from .contracts import EffectiveDatedSpatialAssignment, GeometryAssignmentCandidate


@lru_cache(maxsize=1)
def existing_geometry_ids() -> tuple[str, ...]:
    rows = csv_rows(GEOMETRY_VERSION_CANDIDATES_PATH)
    ids = tuple(row["geometry_version_candidate_id"] for row in rows)
    if len(ids) != len(set(ids)):
        raise ValueError("existing geometry identities must be unique")
    return ids


@lru_cache(maxsize=1)
def derive_geometry_assignments() -> tuple[GeometryAssignmentCandidate, ...]:
    candidates = {row["coordinate_candidate_id"]: row for row in coordinate_candidate_rows()}
    crosswalks = sorted(derive_spatial_canonical_crosswalk(), key=lambda row: sequence_from_id(row.canonical_spatial_point_id))
    start = max((sequence_from_id(value) for value in existing_geometry_ids()), default=0) + 1
    source_sha = sha256_path(COORDINATE_CANDIDATES_PATH)
    out: list[GeometryAssignmentCandidate] = []
    for offset, crosswalk in enumerate(crosswalks):
        candidate = candidates[crosswalk.coordinate_candidate_id]
        geometry_id = f"NG-GEO-{start + offset:06d}"
        payload = {
            "type": "Point",
            "coordinates": [candidate["canonical_longitude"], candidate["canonical_latitude"]],
            "crs_code": "NG-CRS-EPSG4326",
            "subject_id": crosswalk.canonical_spatial_point_id,
        }
        out.append(GeometryAssignmentCandidate(
            geometry_assignment_candidate_id=stable_id(
                "geoassign:nngla:", crosswalk.canonical_spatial_point_id, geometry_id, BUNDLE_EFFECTIVE_DATE
            ),
            coordinate_candidate_id=crosswalk.coordinate_candidate_id,
            canonical_spatial_point_id=crosswalk.canonical_spatial_point_id,
            geometry_id=geometry_id,
            geometry_role_code="SPATIAL_REFERENCE_POINT",
            geometry_type_code="POINT",
            longitude=candidate["canonical_longitude"],
            latitude=candidate["canonical_latitude"],
            crs_code="NG-CRS-EPSG4326",
            source_sha256=source_sha,
            geometry_payload_sha256=payload_sha256(payload),
            valid_from=BUNDLE_EFFECTIVE_DATE,
            valid_to="",
            supersedes_geometry_id="",
            assignment_status="QUALIFIED_CANDIDATE",
            runtime_effect_scope=EFFECT_SCOPE,
        ))
    ids = [row.geometry_id for row in out]
    if set(ids) & set(existing_geometry_ids()):
        raise ValueError("Bundle 17E geometry allocations overlap the immutable existing geometry range")
    if len(ids) != len(set(ids)):
        raise ValueError("Bundle 17E geometry allocation collision")
    return tuple(out)


@lru_cache(maxsize=1)
def geometry_by_candidate() -> dict[str, GeometryAssignmentCandidate]:
    return {row.coordinate_candidate_id: row for row in derive_geometry_assignments()}


@lru_cache(maxsize=1)
def derive_effective_dated_assignments() -> tuple[EffectiveDatedSpatialAssignment, ...]:
    rows = []
    for geometry in derive_geometry_assignments():
        rows.append(EffectiveDatedSpatialAssignment(
            spatial_assignment_id=stable_id(
                "spassign:nngla:", geometry.canonical_spatial_point_id, geometry.geometry_id,
                geometry.geometry_role_code, geometry.valid_from,
            ),
            subject_type="SPATIAL_REFERENCE_POINT",
            subject_id=geometry.canonical_spatial_point_id,
            geometry_id=geometry.geometry_id,
            geometry_role_code=geometry.geometry_role_code,
            effective_from=geometry.valid_from,
            effective_to=geometry.valid_to,
            assignment_version=1,
            assignment_status="QUALIFIED_FOR_PERSISTENCE",
            runtime_effect_scope=EFFECT_SCOPE,
            provenance_reference=geometry.geometry_assignment_candidate_id,
        ))
    return tuple(rows)


__all__ = [
    "existing_geometry_ids", "derive_geometry_assignments", "geometry_by_candidate", "derive_effective_dated_assignments",
]
