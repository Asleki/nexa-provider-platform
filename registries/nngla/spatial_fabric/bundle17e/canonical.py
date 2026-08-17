"""Deterministic Bundle 17E coordinate-candidate -> canonical NG-SPT allocation."""
from __future__ import annotations

from functools import lru_cache

from ._shared import (
    COORDINATE_CANDIDATES_PATH,
    EFFECT_SCOPE,
    ENVIRONMENT_BINDINGS_PATH,
    OCCURRENCE_CROSSWALK_PATH,
    RUNTIME_MODE,
    SPATIAL_DATASET_ID,
    SPATIAL_DATASET_VERSION,
    csv_rows,
    sequence_from_id,
    sha256_path,
    stable_id,
)
from .contracts import SpatialCanonicalCrosswalk, SpatialMigrationAction


@lru_cache(maxsize=1)
def coordinate_candidate_rows() -> tuple[dict[str, str], ...]:
    rows = csv_rows(COORDINATE_CANDIDATES_PATH)
    ids = [row["coordinate_candidate_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("coordinate candidate identities must be unique")
    if any(row["canonicalization_status"] != "CANDIDATE_ONLY_NOT_PERSISTED" for row in rows):
        raise ValueError("Bundle 17E expects non-persisted Bundle 17A coordinate candidates")
    return rows


@lru_cache(maxsize=1)
def existing_spatial_point_mapping() -> dict[str, str]:
    rows = csv_rows(ENVIRONMENT_BINDINGS_PATH)
    mapping = {row["coordinate_candidate_id"]: row["spatial_point_id"] for row in rows}
    if len(mapping) != len(rows):
        raise ValueError("environment binding candidate identities must be unique")
    point_ids = tuple(mapping.values())
    if len(point_ids) != len(set(point_ids)):
        raise ValueError("existing governed spatial point identities must be unique")
    expected = {f"NG-SPT-{number:06d}" for number in range(1, len(point_ids) + 1)}
    if set(point_ids) != expected:
        raise ValueError("existing governed NG-SPT source identities must remain contiguous and preserved")
    return mapping


@lru_cache(maxsize=1)
def derive_spatial_canonical_crosswalk() -> tuple[SpatialCanonicalCrosswalk, ...]:
    candidates = coordinate_candidate_rows()
    existing = existing_spatial_point_mapping()
    next_sequence = max((sequence_from_id(value) for value in existing.values()), default=0) + 1
    out: list[SpatialCanonicalCrosswalk] = []
    for row in candidates:
        candidate_id = row["coordinate_candidate_id"]
        if candidate_id in existing:
            canonical_id = existing[candidate_id]
            origin = "EXISTING_GOVERNED_SOURCE_IDENTITY"
            basis = "EXACT_COORDINATE_MATCH_TO_BUNDLE17A_NG_SPT_IDENTITY"
        else:
            canonical_id = f"NG-SPT-{next_sequence:06d}"
            next_sequence += 1
            origin = "NEW_BUNDLE17E_ALLOCATION"
            basis = "DETERMINISTIC_APPEND_AFTER_EXISTING_GOVERNED_NG_SPT_RANGE"
        out.append(SpatialCanonicalCrosswalk(
            spatial_crosswalk_id=stable_id("crosswalk:nngla:", candidate_id, canonical_id),
            coordinate_candidate_id=candidate_id,
            canonical_spatial_point_id=canonical_id,
            canonical_version=1,
            crosswalk_basis=basis,
            identity_origin=origin,
            source_dataset_id=SPATIAL_DATASET_ID,
            source_dataset_version=SPATIAL_DATASET_VERSION,
            source_artifact_sha256=sha256_path(COORDINATE_CANDIDATES_PATH),
            occurrence_crosswalk_sha256=sha256_path(OCCURRENCE_CROSSWALK_PATH),
            runtime_mode=RUNTIME_MODE,
            effect_scope=EFFECT_SCOPE,
            status="QUALIFIED_FOR_PERSISTENCE",
        ))
    canonical_ids = [row.canonical_spatial_point_id for row in out]
    if len(canonical_ids) != len(set(canonical_ids)):
        raise ValueError("canonical spatial allocation collision")
    expected = {f"NG-SPT-{number:06d}" for number in range(1, len(out) + 1)}
    if set(canonical_ids) != expected:
        raise ValueError("initial Bundle 17E canonical spatial allocation must preserve and extend the locked sequence")
    return tuple(out)


@lru_cache(maxsize=1)
def canonical_by_candidate() -> dict[str, SpatialCanonicalCrosswalk]:
    return {row.coordinate_candidate_id: row for row in derive_spatial_canonical_crosswalk()}


def migration_action_rows() -> tuple[dict[str, str], ...]:
    """Offline planned action; live target state must still be inspected before execution."""
    return tuple({
        "migration_action_id": stable_id("spaction:nngla:", row.coordinate_candidate_id, SpatialMigrationAction.INSERT_NEW.value),
        "coordinate_candidate_id": row.coordinate_candidate_id,
        "canonical_spatial_point_id": row.canonical_spatial_point_id,
        "planned_action": SpatialMigrationAction.INSERT_NEW.value,
        "allocation_basis": row.crosswalk_basis,
        "identity_origin": row.identity_origin,
        "requires_live_target_confirmation": "true",
        "existing_canonical_rows_destructively_updated": "false",
        "runtime_mode": row.runtime_mode,
        "effect_scope": row.effect_scope,
        "status": "PLANNED_NOT_EXECUTED",
    } for row in derive_spatial_canonical_crosswalk())


__all__ = [
    "coordinate_candidate_rows", "existing_spatial_point_mapping", "derive_spatial_canonical_crosswalk",
    "canonical_by_candidate", "migration_action_rows",
]
