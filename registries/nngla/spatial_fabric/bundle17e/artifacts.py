"""Materialize the ten governed Bundle 17E CSV contracts/evidence registers."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv

from ._shared import BASE_REPOSITORY_REVISION, BUNDLE17E_INPUT_PATHS, SOURCE_ROOT
from .batch import offline_spatial_preview
from .canonical import derive_spatial_canonical_crosswalk, migration_action_rows
from .contracts import SpatialMigrationAction
from .geometry import derive_effective_dated_assignments, derive_geometry_assignments
from .qualification import derive_persistence_qualifications


ARTIFACT_PATHS = {
    "migration_actions": SOURCE_ROOT / "09_execution" / "novegeo_spatial_migration_actions_v002.csv",
    "canonical_crosswalk": SOURCE_ROOT / "08_relationships" / "novegeo_spatial_canonical_crosswalk_v001.csv",
    "geometry_assignments": SOURCE_ROOT / "08_relationships" / "novegeo_geometry_assignment_candidates_v002.csv",
    "effective_assignments": SOURCE_ROOT / "08_relationships" / "novegeo_effective_dated_spatial_assignments_v001.csv",
    "persistence_qualification": SOURCE_ROOT / "10_evidence" / "novegeo_spatial_persistence_qualification_v001.csv",
    "batch_manifest": SOURCE_ROOT / "00_manifest" / "novegeo_spatial_batch_manifest_v001.csv",
    "spatial_qualification": SOURCE_ROOT / "10_evidence" / "novegeo_spatial_qualification_results_v002.csv",
    "quarantine": SOURCE_ROOT / "09_quarantine" / "novegeo_spatial_quarantine_v001.csv",
    "execution_receipts": SOURCE_ROOT / "10_evidence" / "novegeo_spatial_execution_receipts_v001.csv",
    "execution_items": SOURCE_ROOT / "10_evidence" / "novegeo_spatial_execution_items_v001.csv",
}

EMPTY_FIELDNAMES = {
    "quarantine": (
        "quarantine_id", "coordinate_candidate_id", "canonical_spatial_point_id", "geometry_id", "error_code",
        "error_message", "fingerprint", "runtime_mode", "effect_scope", "status",
    ),
    "execution_receipts": (
        "execution_id", "plan_id", "plan_version", "fingerprint", "content_fingerprint", "database_name",
        "environment_name", "runtime_mode", "repository_revision", "source_sha256", "submitter_actor_id",
        "approver_actor_id", "selected_count", "inserted_count", "reused_count", "quarantined_count", "failed_count",
        "status", "started_at", "completed_at",
    ),
    "execution_items": (
        "execution_id", "coordinate_candidate_id", "canonical_spatial_point_id", "geometry_id", "outcome", "detail",
    ),
}


def _serialize(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, SpatialMigrationAction):
        return value.value
    return str(value)


def _rows(values) -> tuple[dict[str, str], ...]:
    out = []
    for item in values:
        raw = asdict(item) if not isinstance(item, dict) else item
        out.append({key: _serialize(value) for key, value in raw.items()})
    return tuple(out)


def artifact_rows() -> dict[str, tuple[dict[str, str], ...]]:
    preview = offline_spatial_preview()
    spatial_qualification = tuple({
        "coordinate_candidate_id": item.coordinate_candidate_id,
        "canonical_spatial_point_id": item.canonical_spatial_point_id,
        "geometry_id": item.geometry_id,
        "migration_action": item.migration_action.value,
        "selected": str(item.selected).lower(),
        "source_verified": str(item.source_verified).lower(),
        "coordinate_valid": str(item.coordinate_valid).lower(),
        "map_reconciled": str(item.map_reconciled).lower(),
        "crs_valid": str(item.crs_valid).lower(),
        "precision_valid": str(item.precision_valid).lower(),
        "containment_valid": str(item.containment_valid).lower(),
        "topology_valid": str(item.topology_valid).lower(),
        "environment_resolved": str(item.environment_resolved).lower(),
        "conflict_free": str(item.conflict_free).lower(),
        "qualified": str(item.qualified).lower(),
        "quarantined": str(item.quarantined).lower(),
        "quarantine_reason": item.quarantine_reason,
        "database_writes": str(item.database_writes),
        "fingerprint": item.fingerprint,
    } for item in preview.items)
    batch_manifest = ({
        "batch_id": preview.batch_id,
        "plan_id": "P006.7.11.7.7-8-BUNDLE17E",
        "plan_version": "1",
        "source_sha256": preview.source_sha256,
        "input_artifact_count": str(len(BUNDLE17E_INPUT_PATHS)),
        "selected_count": str(preview.selected_count),
        "qualified_count": str(preview.qualified_count),
        "quarantined_count": str(preview.quarantined_count),
        "planned_insert_new_count": str(preview.insert_new_count),
        "planned_reuse_count": str(preview.reuse_count),
        "database_writes": "0",
        "database_name": preview.database_name,
        "environment_name": preview.environment_name,
        "repository_revision": BASE_REPOSITORY_REVISION,
        "target_snapshot_digest": preview.target_snapshot_digest,
        "content_fingerprint": preview.content_fingerprint,
        "fingerprint": preview.fingerprint,
        "schema_ready": str(preview.schema_ready).lower(),
        "execution_ready": str(preview.execution_ready).lower(),
        "execution_state": "NOT_EXECUTED_LIVE_TARGET_CONFIRMATION_REQUIRED",
    },)
    return {
        "migration_actions": tuple(migration_action_rows()),
        "canonical_crosswalk": _rows(derive_spatial_canonical_crosswalk()),
        "geometry_assignments": _rows(derive_geometry_assignments()),
        "effective_assignments": _rows(derive_effective_dated_assignments()),
        "persistence_qualification": _rows(derive_persistence_qualifications()),
        "batch_manifest": batch_manifest,
        "spatial_qualification": spatial_qualification,
        "quarantine": (),
        "execution_receipts": (),
        "execution_items": (),
    }


def _write(path: Path, rows: tuple[dict[str, str], ...], fieldnames: tuple[str, ...] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = tuple(rows[0]) if rows else fieldnames
    if not names:
        raise ValueError(f"no governed header contract for {path.name}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)


def write_bundle17e_artifacts(source_root: Path = SOURCE_ROOT) -> tuple[Path, ...]:
    rows = artifact_rows()
    written = []
    for key, canonical_path in ARTIFACT_PATHS.items():
        relative = canonical_path.relative_to(SOURCE_ROOT)
        path = source_root / relative
        _write(path, rows[key], EMPTY_FIELDNAMES.get(key))
        written.append(path)
    return tuple(written)


def _read(path: Path) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), tuple(dict(row) for row in reader)


def artifact_drift_findings(source_root: Path = SOURCE_ROOT) -> tuple[str, ...]:
    expected = artifact_rows()
    findings = []
    for key, canonical_path in ARTIFACT_PATHS.items():
        path = source_root / canonical_path.relative_to(SOURCE_ROOT)
        if not path.is_file():
            findings.append(f"MISSING:{path}")
            continue
        header, actual = _read(path)
        expected_header = tuple(expected[key][0]) if expected[key] else EMPTY_FIELDNAMES[key]
        if header != expected_header or actual != expected[key]:
            findings.append(f"DRIFT:{path}")
    return tuple(findings)


__all__ = ["ARTIFACT_PATHS", "EMPTY_FIELDNAMES", "artifact_rows", "write_bundle17e_artifacts", "artifact_drift_findings"]
