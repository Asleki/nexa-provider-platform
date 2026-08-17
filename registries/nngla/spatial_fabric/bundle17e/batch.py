"""Governed zero-write spatial batch preview and fail-closed fingerprinting."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json

from ._shared import (
    BASE_REPOSITORY_REVISION,
    BUNDLE17E_INPUT_PATHS,
    COORDINATE_CANDIDATES_PATH,
    EFFECT_SCOPE,
    REQUIRED_SCHEMA_CAPABILITIES,
    RUNTIME_MODE,
    sha256_path,
    stable_id,
)
from .canonical import canonical_by_candidate
from .contracts import SpatialBatchPreview, SpatialMigrationAction, SpatialQualificationResult, TargetSpatialSnapshot
from .geometry import geometry_by_candidate
from .qualification import derive_persistence_qualifications


@lru_cache(maxsize=1)
def content_fingerprint() -> str:
    payload = {
        "input_artifact_hashes": [(str(path.name), sha256_path(path)) for path in BUNDLE17E_INPUT_PATHS],
        "source_sha256": sha256_path(COORDINATE_CANDIDATES_PATH),
        "selected": [row.coordinate_candidate_id for row in derive_persistence_qualifications()],
        "canonical": [
            (row.coordinate_candidate_id, row.canonical_spatial_point_id)
            for row in derive_persistence_qualifications()
        ],
        "geometry": [
            (row.coordinate_candidate_id, row.geometry_id)
            for row in derive_persistence_qualifications()
        ],
        "runtime_mode": RUNTIME_MODE,
        "effect_scope": EFFECT_SCOPE,
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()



def _resolve_action(
    candidate_id: str,
    canonical_id: str,
    geometry_id: str,
    target: TargetSpatialSnapshot,
) -> tuple[SpatialMigrationAction, str]:
    if not target.available:
        return SpatialMigrationAction.INSERT_NEW, "TARGET_STATE_UNRESOLVED_LIVE_CONFIRMATION_REQUIRED"

    mapped = target.candidate_crosswalks.get(candidate_id)
    subject_geometry = target.geometry_by_subject.get(canonical_id)
    canonical_occupied = canonical_id in target.occupied_spatial_ids
    geometry_occupied = geometry_id in target.occupied_geometry_ids

    if mapped is not None:
        if mapped != canonical_id:
            return SpatialMigrationAction.QUARANTINE, "TARGET_CROSSWALK_DISAGREES_WITH_LOCKED_CANONICAL_ID"
        if not canonical_occupied:
            return SpatialMigrationAction.QUARANTINE, "TARGET_CROSSWALK_EXISTS_WITHOUT_CANONICAL_SPATIAL_ROW"
        if subject_geometry != geometry_id:
            return SpatialMigrationAction.QUARANTINE, "TARGET_CANONICAL_POINT_GEOMETRY_DISAGREES_WITH_LOCKED_ASSIGNMENT"
        if not geometry_occupied:
            return SpatialMigrationAction.QUARANTINE, "TARGET_GEOMETRY_LINK_EXISTS_WITHOUT_GEOMETRY_ROW"
        return SpatialMigrationAction.REUSE_CANONICAL, "EXACT_CANONICAL_TARGET_STATE_REUSE"

    if canonical_occupied:
        return SpatialMigrationAction.QUARANTINE, "CANONICAL_SPATIAL_ID_ALREADY_OCCUPIED_WITHOUT_EXPECTED_CROSSWALK"
    if geometry_occupied:
        return SpatialMigrationAction.QUARANTINE, "GEOMETRY_ID_ALREADY_OCCUPIED_WITHOUT_EXPECTED_ASSIGNMENT"
    if subject_geometry:
        return SpatialMigrationAction.QUARANTINE, "SUBJECT_ALREADY_HAS_UNEXPECTED_SPATIAL_REFERENCE_GEOMETRY"
    return SpatialMigrationAction.INSERT_NEW, "TARGET_IDS_AVAILABLE_FOR_INSERT"


def build_spatial_preview(
    target: TargetSpatialSnapshot | None = None,
    *,
    repository_revision: str = BASE_REPOSITORY_REVISION,
) -> SpatialBatchPreview:
    target = target or TargetSpatialSnapshot.unavailable()
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    persistence = derive_persistence_qualifications()

    preliminary: list[dict[str, object]] = []
    for row in persistence:
        action, reason = _resolve_action(
            row.coordinate_candidate_id,
            row.canonical_spatial_point_id,
            row.geometry_id,
            target,
        )
        qualified = row.qualification_status == "PASS" and action is not SpatialMigrationAction.QUARANTINE
        preliminary.append({
            "row": row,
            "action": action,
            "qualified": qualified,
            "quarantined": action is SpatialMigrationAction.QUARANTINE or row.qualification_status != "PASS",
            "reason": reason if action is SpatialMigrationAction.QUARANTINE else (row.findings or ""),
        })

    schema_ready = target.available and REQUIRED_SCHEMA_CAPABILITIES.issubset(target.schema_capabilities)
    quarantine_count = sum(bool(item["quarantined"]) for item in preliminary)
    execution_ready = target.available and schema_ready and quarantine_count == 0 and all(bool(item["qualified"]) for item in preliminary)

    fingerprint_payload = {
        "content_fingerprint": content_fingerprint(),
        "target_snapshot_digest": target.digest,
        "repository_revision": repository_revision,
        "runtime_mode": RUNTIME_MODE,
        "effect_scope": EFFECT_SCOPE,
        "actions": [
            (
                item["row"].coordinate_candidate_id,
                item["row"].canonical_spatial_point_id,
                item["row"].geometry_id,
                item["action"].value,
            )
            for item in preliminary
        ],
    }
    fingerprint = sha256(json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    items = tuple(
        SpatialQualificationResult(
            coordinate_candidate_id=item["row"].coordinate_candidate_id,
            canonical_spatial_point_id=item["row"].canonical_spatial_point_id,
            geometry_id=item["row"].geometry_id,
            migration_action=item["action"],
            selected=True,
            source_verified=item["row"].source_verified,
            coordinate_valid=item["row"].coordinate_valid,
            map_reconciled=item["row"].map_reconciled,
            crs_valid=item["row"].crs_valid,
            precision_valid=item["row"].precision_valid,
            containment_valid=item["row"].containment_valid,
            topology_valid=item["row"].topology_valid,
            environment_resolved=item["row"].environment_resolved,
            conflict_free=item["row"].conflict_free,
            qualified=bool(item["qualified"]),
            quarantined=bool(item["quarantined"]),
            quarantine_reason=str(item["reason"]),
            database_writes=0,
            fingerprint=fingerprint,
        )
        for item in preliminary
    )
    counts = Counter(item.migration_action.value for item in items)
    return SpatialBatchPreview(
        batch_id=stable_id("spbatch:nngla:", content_fingerprint(), target.digest, repository_revision),
        selected_count=len(items),
        qualified_count=sum(item.qualified for item in items),
        quarantined_count=sum(item.quarantined for item in items),
        insert_new_count=counts[SpatialMigrationAction.INSERT_NEW.value],
        reuse_count=counts[SpatialMigrationAction.REUSE_CANONICAL.value],
        database_writes=0,
        database_name=target.database_name,
        environment_name=target.environment_name,
        repository_revision=repository_revision,
        target_snapshot_digest=target.digest,
        content_fingerprint=content_fingerprint(),
        fingerprint=fingerprint,
        source_sha256=sha256_path(COORDINATE_CANDIDATES_PATH),
        schema_ready=schema_ready,
        execution_ready=execution_ready,
        items=items,
    )


@lru_cache(maxsize=1)
def offline_spatial_preview() -> SpatialBatchPreview:
    return build_spatial_preview(TargetSpatialSnapshot.unavailable())


__all__ = ["content_fingerprint", "build_spatial_preview", "offline_spatial_preview"]
