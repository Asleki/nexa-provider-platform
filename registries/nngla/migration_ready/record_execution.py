"""NPP-style deterministic record-atomic NNGLA spatial migration."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from registries.nngla.spatial_fabric.bundle17e._shared import (
    COORDINATE_CANDIDATES_PATH,
    RUNTIME_MODE,
    sha256_path,
)
from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate
from registries.nngla.spatial_fabric.bundle17e.contracts import (
    SpatialExecutionItem,
    SpatialExecutionReceipt,
)
from registries.nngla.spatial_fabric.bundle17e.geometry import geometry_by_candidate
from registries.nngla.spatial_fabric.bundle17e.qualification import bundle17e_is_qualified

from .contracts import ReconciliationAction
from .record_contracts import RecordExecutionResult, RecordWindowPreview
from .record_persistence import RecordAtomicPersistence
from .record_progress import (
    assess_record_progress,
    canonical_migration_order,
    ordinal_maps,
    select_record_window,
)
from .reconciliation import assert_no_conflicts, reconcile_spatial_target

PLAN_ID = "P006.7.11.7.0MR-SPATIAL-BATCH"
PLAN_VERSION = 3


class RecordMigrationError(RuntimeError):
    pass


class RecordExecutionInterrupted(RecordMigrationError):
    def __init__(
        self,
        *,
        failed_ordinal: int,
        inserted_count: int,
        reused_count: int,
        last_committed_ordinal: int | None,
        cause: BaseException,
    ) -> None:
        self.failed_ordinal = failed_ordinal
        self.inserted_count = inserted_count
        self.reused_count = reused_count
        self.last_committed_ordinal = last_committed_ordinal
        self.cause = cause
        super().__init__(
            f"record migration interrupted at ordinal {failed_ordinal}; "
            f"this process observed {inserted_count} inserted and {reused_count} reused before interruption: {cause}"
        )


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_confirmation_token(database_name: str, logical_batch_id: str | None, fingerprint: str) -> str:
    batch = logical_batch_id or "MIGRATION-COMPLETE"
    return f"MIGRATE-NNGLA-RECORDS::{database_name}::{batch}::{fingerprint}"


def _record_receipt_fingerprint(
    *,
    logical_batch_id: str,
    migration_ordinal: int,
    candidate_id: str,
    canonical_id: str,
    geometry_id: str,
    source_sha256: str,
) -> str:
    material = "|".join(
        (
            PLAN_ID,
            str(PLAN_VERSION),
            logical_batch_id,
            str(migration_ordinal),
            candidate_id,
            canonical_id,
            geometry_id,
            source_sha256,
        )
    )
    return sha256(material.encode("utf-8")).hexdigest()


def _preview_fingerprint(
    *,
    database_name: str,
    environment_name: str,
    source_sha256: str,
    repository_revision: str,
    requested_count: int,
    progress,
    window,
    selected,
) -> str:
    payload = {
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "database_name": database_name,
        "environment_name": environment_name,
        "source_sha256": source_sha256,
        "repository_revision": repository_revision,
        "requested_count": requested_count,
        "contiguous_completed_ordinal": progress.contiguous_completed_ordinal,
        "first_unfulfilled_ordinal": progress.first_unfulfilled_ordinal,
        "active_logical_batch_id": progress.active_logical_batch_id,
        "window": None
        if window is None
        else {
            "logical_batch_id": window.logical_batch_id,
            "window_start_ordinal": window.window_start_ordinal,
            "window_end_ordinal": window.window_end_ordinal,
            "requested_count": window.requested_count,
            "execution_start_ordinal": window.execution_start_ordinal,
            "execution_end_ordinal": window.execution_end_ordinal,
            "candidate_ids": list(window.candidate_ids),
            "resumed": window.resumed,
            "explicit_range": window.explicit_range,
        },
        "selected": [
            {
                "candidate": item.coordinate_candidate_id,
                "canonical": item.canonical_spatial_point_id,
                "geometry": item.geometry_id,
                "action": item.action.value,
                "reason": item.reason,
            }
            for item in selected
        ],
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_record_preview(
    repository,
    *,
    database_name: str,
    environment_name: str,
    repository_revision: str,
    requested_count: int,
    start_ordinal: int | None = None,
) -> RecordWindowPreview:
    if not bundle17e_is_qualified():
        raise RecordMigrationError("locked Bundle 17E source qualification is not green")
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    if len(crosswalks) != 2411 or len(geometries) != 2411:
        raise RecordMigrationError("locked spatial source must contain exactly 2,411 candidates")

    persistence = RecordAtomicPersistence(repository)
    target = persistence.snapshot(database_name, environment_name)
    reconciliation = reconcile_spatial_target(target, crosswalks, geometries)
    assert_no_conflicts(reconciliation)
    candidate_ids = canonical_migration_order(crosswalks)
    observations = persistence.record_receipt_observations(
        plan_id=PLAN_ID,
        plan_version=PLAN_VERSION,
        database_name=database_name,
        environment_name=environment_name,
    )
    progress = assess_record_progress(
        candidate_ids=candidate_ids,
        reconciliation=reconciliation,
        observations=observations,
    )
    source_sha = sha256_path(COORDINATE_CANDIDATES_PATH)
    window = select_record_window(
        candidate_ids=candidate_ids,
        progress=progress,
        requested_count=requested_count,
        plan_id=PLAN_ID,
        plan_version=PLAN_VERSION,
        source_sha256=source_sha,
        start_ordinal=start_ordinal,
    )
    by_id = {item.coordinate_candidate_id: item for item in reconciliation}
    selected = tuple(by_id[candidate_id] for candidate_id in (() if window is None else window.candidate_ids))
    insert_count = sum(item.action is ReconciliationAction.INSERT_NEW for item in selected)
    reuse_count = sum(item.action is ReconciliationAction.REUSE_CANONICAL for item in selected)
    conflict_count = sum(item.action is ReconciliationAction.CONFLICT for item in selected)
    fingerprint = _preview_fingerprint(
        database_name=database_name,
        environment_name=environment_name,
        source_sha256=source_sha,
        repository_revision=repository_revision,
        requested_count=requested_count,
        progress=progress,
        window=window,
        selected=selected,
    )
    return RecordWindowPreview(
        database_name=database_name,
        environment_name=environment_name,
        source_sha256=source_sha,
        repository_revision=repository_revision,
        requested_count=requested_count,
        progress=progress,
        window=window,
        selected_count=len(selected),
        insert_count=insert_count,
        reuse_count=reuse_count,
        conflict_count=conflict_count,
        fingerprint=fingerprint,
    )


def execute_records(
    repository,
    *,
    database_name: str,
    environment_name: str,
    repository_revision: str,
    requested_count: int,
    approved_fingerprint: str,
    confirmation: str,
    submitter_actor_id: str,
    approver_actor_id: str,
    start_ordinal: int | None = None,
) -> RecordExecutionResult:
    if not submitter_actor_id or not approver_actor_id:
        raise RecordMigrationError("submitter and approver are required")
    if submitter_actor_id == approver_actor_id:
        raise RecordMigrationError("submitter and approver must remain separate")

    preview = build_record_preview(
        repository,
        database_name=database_name,
        environment_name=environment_name,
        repository_revision=repository_revision,
        requested_count=requested_count,
        start_ordinal=start_ordinal,
    )
    if preview.fingerprint != approved_fingerprint:
        raise RecordMigrationError("approved record-window fingerprint is stale or does not match target")
    logical_batch_id = preview.window.logical_batch_id if preview.window is not None else None
    if confirmation != record_confirmation_token(database_name, logical_batch_id, preview.fingerprint):
        raise RecordMigrationError("NNGLA record migration confirmation token does not match")
    if not preview.execution_ready:
        raise RecordMigrationError("record migration preview is not execution-ready")
    if preview.window is None:
        return RecordExecutionResult(
            logical_batch_id=None,
            window_start_ordinal=None,
            window_end_ordinal=None,
            execution_start_ordinal=None,
            execution_end_ordinal=None,
            selected_count=0,
            inserted_count=0,
            reused_count=0,
            last_committed_ordinal=preview.progress.contiguous_completed_ordinal,
            status="MIGRATION_COMPLETE",
        )

    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    candidate_ids = canonical_migration_order(crosswalks)
    by_candidate_ordinal, _ = ordinal_maps(candidate_ids)
    source_sha = preview.source_sha256
    source_path = str(COORDINATE_CANDIDATES_PATH.relative_to(Path(__file__).resolve().parents[3]))
    source_size = COORDINATE_CANDIDATES_PATH.stat().st_size
    persistence = RecordAtomicPersistence(repository)
    persistence.ensure_source_contract(source_sha, source_path, 2411, source_size)

    inserted = 0
    reused = 0
    last_committed = preview.progress.contiguous_completed_ordinal or None

    for candidate_id in preview.window.candidate_ids:
        ordinal = by_candidate_ordinal[candidate_id]
        crosswalk = crosswalks[candidate_id]
        geometry = geometries[candidate_id]
        try:
            current = persistence.classify_record(
                database_name=database_name,
                environment_name=environment_name,
                crosswalk=crosswalk,
                geometry=geometry,
            )
            if current.action is ReconciliationAction.CONFLICT:
                raise RecordMigrationError(
                    f"record {ordinal} conflicts with PostgreSQL: {current.reason}"
                )
            if current.action is ReconciliationAction.REUSE_CANONICAL:
                reused += 1
                last_committed = max(last_committed or 0, ordinal)
                continue

            started = _utc()
            receipt_fingerprint = _record_receipt_fingerprint(
                logical_batch_id=preview.window.logical_batch_id,
                migration_ordinal=ordinal,
                candidate_id=candidate_id,
                canonical_id=crosswalk.canonical_spatial_point_id,
                geometry_id=geometry.geometry_id,
                source_sha256=source_sha,
            )
            execution_id = "nnglarun:spatial:mr:" + receipt_fingerprint[:24]
            with persistence.transaction() as base:
                outcome = base.persist_point(crosswalk, geometry)
                if outcome not in {"INSERTED", "REUSED"}:
                    raise RecordMigrationError(f"unexpected persistence outcome for record {ordinal}: {outcome}")
                verified = persistence.classify_record(
                    database_name=database_name,
                    environment_name=environment_name,
                    crosswalk=crosswalk,
                    geometry=geometry,
                )
                if verified.action is not ReconciliationAction.REUSE_CANONICAL:
                    raise RecordMigrationError(
                        f"post-write verification failed for record {ordinal}: {verified.reason}"
                    )
                completed = _utc()
                item = SpatialExecutionItem(
                    coordinate_candidate_id=candidate_id,
                    canonical_spatial_point_id=crosswalk.canonical_spatial_point_id,
                    geometry_id=geometry.geometry_id,
                    outcome="INSERTED",
                    detail=(
                        f"logical_batch_id={preview.window.logical_batch_id};"
                        f"window_start_ordinal={preview.window.window_start_ordinal};"
                        f"window_end_ordinal={preview.window.window_end_ordinal};"
                        f"requested_count={preview.window.requested_count};"
                        f"migration_ordinal={ordinal};"
                        f"authorization_fingerprint={preview.fingerprint};"
                        "source_order=canonical_ng_spt"
                    ),
                )
                receipt = SpatialExecutionReceipt(
                    execution_id=execution_id,
                    plan_id=PLAN_ID,
                    plan_version=PLAN_VERSION,
                    fingerprint=receipt_fingerprint,
                    content_fingerprint=sha256(candidate_id.encode("utf-8")).hexdigest(),
                    database_name=database_name,
                    environment_name=environment_name,
                    runtime_mode=RUNTIME_MODE,
                    repository_revision=repository_revision,
                    source_sha256=source_sha,
                    submitter_actor_id=submitter_actor_id,
                    approver_actor_id=approver_actor_id,
                    selected_count=1,
                    inserted_count=1,
                    reused_count=0,
                    quarantined_count=0,
                    failed_count=0,
                    status="APPLIED",
                    started_at=started,
                    completed_at=completed,
                    items=(item,),
                )
                base.persist_execution_receipt(receipt)
            inserted += 1
            last_committed = max(last_committed or 0, ordinal)
        except Exception as exc:
            if isinstance(exc, RecordMigrationError) and not inserted and not reused:
                raise
            raise RecordExecutionInterrupted(
                failed_ordinal=ordinal,
                inserted_count=inserted,
                reused_count=reused,
                last_committed_ordinal=last_committed,
                cause=exc,
            ) from exc

    status = "REUSED" if inserted == 0 else "COMPLETE"
    return RecordExecutionResult(
        logical_batch_id=preview.window.logical_batch_id,
        window_start_ordinal=preview.window.window_start_ordinal,
        window_end_ordinal=preview.window.window_end_ordinal,
        execution_start_ordinal=preview.window.execution_start_ordinal,
        execution_end_ordinal=preview.window.execution_end_ordinal,
        selected_count=preview.window.selected_count,
        inserted_count=inserted,
        reused_count=reused,
        last_committed_ordinal=last_committed,
        status=status,
    )


__all__ = [
    "PLAN_ID",
    "PLAN_VERSION",
    "RecordMigrationError",
    "RecordExecutionInterrupted",
    "record_confirmation_token",
    "build_record_preview",
    "execute_records",
]
