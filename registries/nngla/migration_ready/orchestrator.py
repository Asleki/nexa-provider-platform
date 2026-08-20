"""Resumable per-transaction execution of the locked 2,411-point spatial fabric."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
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

from .batching import build_fixed_windows, build_profile_windows, ordered_candidate_ids
from .catalogue import get_batch_profile
from .contracts import (
    BatchExecutionResult,
    MigrationPreview,
    ReconciliationAction,
)
from .reconciliation import assert_no_conflicts, reconcile_spatial_target

PLAN_ID = "P006.7.11.7.0MR-SPATIAL-BATCH"
PLAN_VERSION = 2


class MigrationReadyExecutionError(RuntimeError):
    pass


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot(repository, database_name: str, environment_name: str):
    try:
        return repository.snapshot(database_name, environment_name)
    except TypeError:
        return repository.snapshot()


def confirmation_token(database_name: str, fingerprint: str) -> str:
    return f"MIGRATE-NNGLA-2411::{database_name}::{fingerprint}"


def build_spatial_preview(
    repository,
    *,
    database_name: str,
    environment_name: str,
    repository_revision: str,
    profile_id: str = "initial-spatial-2411",
    batch_size: int | None = None,
) -> MigrationPreview:
    if not bundle17e_is_qualified():
        raise MigrationReadyExecutionError("locked Bundle 17E source qualification is not green")

    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    if len(crosswalks) != 2411 or len(geometries) != 2411:
        raise MigrationReadyExecutionError("locked spatial source must contain exactly 2,411 candidates")

    target = _snapshot(repository, database_name, environment_name)
    reconciliation = reconcile_spatial_target(target, crosswalks, geometries)
    candidate_ids = ordered_candidate_ids(crosswalks)
    if batch_size is None:
        profile = get_batch_profile(profile_id)
        windows = build_profile_windows(candidate_ids, profile)
        effective_profile_id = profile.profile_id
    else:
        windows = build_fixed_windows(candidate_ids, batch_size)
        effective_profile_id = f"fixed-{batch_size}"

    return MigrationPreview.build(
        database_name=database_name,
        environment_name=environment_name,
        profile_id=effective_profile_id,
        source_sha256=sha256_path(COORDINATE_CANDIDATES_PATH),
        repository_revision=repository_revision,
        batches=windows,
        reconciliation=reconciliation,
    )


def _batch_digest(candidate_ids: tuple[str, ...]) -> str:
    return sha256("\n".join(candidate_ids).encode("utf-8")).hexdigest()


def _batch_receipt_fingerprint(
    authorization_fingerprint: str,
    batch_number: int,
    candidate_ids: tuple[str, ...],
) -> str:
    """Return the durable identity for one transaction under an approved preview.

    Bundle 17.0MR used the whole-preview authorization fingerprint for every
    independently committed batch receipt. PostgreSQL correctly rejects that
    because execution receipt fingerprints are unique per target. 17.1MR keeps
    the preview fingerprint as the operator authorization identity while
    deriving a deterministic receipt fingerprint for each batch.
    """
    material = "|".join(
        (
            PLAN_ID,
            str(PLAN_VERSION),
            authorization_fingerprint,
            str(batch_number),
            _batch_digest(candidate_ids),
        )
    )
    return sha256(material.encode("utf-8")).hexdigest()


def _assert_batch_committed_state(
    repository,
    *,
    database_name: str,
    environment_name: str,
    candidate_ids: tuple[str, ...],
) -> None:
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    state = _snapshot(repository, database_name, environment_name)
    reconciliation = reconcile_spatial_target(state, crosswalks, geometries)
    by_id = {item.coordinate_candidate_id: item for item in reconciliation}
    bad = [
        candidate_id
        for candidate_id in candidate_ids
        if candidate_id not in by_id
        or by_id[candidate_id].action is not ReconciliationAction.REUSE_CANONICAL
    ]
    if bad:
        raise MigrationReadyExecutionError(
            "post-write target verification failed before commit for: " + ", ".join(bad[:8])
        )


def execute_spatial(
    repository,
    *,
    database_name: str,
    environment_name: str,
    repository_revision: str,
    approved_fingerprint: str,
    confirmation: str,
    submitter_actor_id: str,
    approver_actor_id: str,
    profile_id: str = "initial-spatial-2411",
    batch_size: int | None = None,
) -> tuple[BatchExecutionResult, ...]:
    if not submitter_actor_id or not approver_actor_id:
        raise MigrationReadyExecutionError("submitter and approver are required")
    if submitter_actor_id == approver_actor_id:
        raise MigrationReadyExecutionError("submitter and approver must remain separate")

    preview = build_spatial_preview(
        repository,
        database_name=database_name,
        environment_name=environment_name,
        repository_revision=repository_revision,
        profile_id=profile_id,
        batch_size=batch_size,
    )
    if preview.fingerprint != approved_fingerprint:
        raise MigrationReadyExecutionError("approved preview fingerprint is stale or does not match target")
    expected_confirmation = confirmation_token(database_name, preview.fingerprint)
    if confirmation != expected_confirmation:
        raise MigrationReadyExecutionError("NNGLA Migration Ready confirmation token does not match")
    if not preview.execution_ready:
        raise MigrationReadyExecutionError("spatial migration preview is not execution-ready")

    assert_no_conflicts(preview.reconciliation)
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    source_sha = preview.source_sha256
    source_path = str(COORDINATE_CANDIDATES_PATH.relative_to(Path(__file__).resolve().parents[3]))
    source_size = COORDINATE_CANDIDATES_PATH.stat().st_size
    results: list[BatchExecutionResult] = []

    for window in preview.batches:
        fresh = reconcile_spatial_target(
            _snapshot(repository, database_name, environment_name),
            crosswalks,
            geometries,
        )
        assert_no_conflicts(fresh)
        by_id = {item.coordinate_candidate_id: item for item in fresh}
        selected = tuple(by_id[candidate_id] for candidate_id in window.candidate_ids)
        # An already committed batch is a true zero-write skip. PostgreSQL state,
        # not a local checkpoint, is the resume authority.
        if all(item.action is ReconciliationAction.REUSE_CANONICAL for item in selected):
            results.append(
                BatchExecutionResult(
                    batch_number=window.batch_number,
                    selected_count=window.selected_count,
                    inserted_count=0,
                    reused_count=window.selected_count,
                    status="REUSED",
                    execution_id="REUSED_POSTGRESQL_STATE",
                    candidate_ids=window.candidate_ids,
                )
            )
            continue

        started = _utc()
        inserted = 0
        reused = 0
        execution_items: list[SpatialExecutionItem] = []

        with repository.transaction():
            if hasattr(repository, "ensure_source_contract"):
                repository.ensure_source_contract(source_sha, source_path, 2411, source_size)

            for item in selected:
                if item.action is ReconciliationAction.INSERT_NEW:
                    outcome = repository.persist_point(
                        crosswalks[item.coordinate_candidate_id],
                        geometries[item.coordinate_candidate_id],
                    )
                    if outcome not in {"INSERTED", "REUSED"}:
                        raise MigrationReadyExecutionError(f"unexpected persistence outcome: {outcome}")
                    if outcome == "INSERTED":
                        inserted += 1
                    else:
                        reused += 1
                elif item.action is ReconciliationAction.REUSE_CANONICAL:
                    outcome = "REUSED"
                    reused += 1
                else:
                    raise MigrationReadyExecutionError(
                        f"conflicting candidate reached execution: {item.coordinate_candidate_id}"
                    )
                execution_items.append(
                    SpatialExecutionItem(
                        coordinate_candidate_id=item.coordinate_candidate_id,
                        canonical_spatial_point_id=item.canonical_spatial_point_id,
                        geometry_id=item.geometry_id,
                        outcome=outcome,
                        detail=(
                            f"batch={window.batch_number};profile={preview.profile_id};"
                            f"authorization_fingerprint={preview.fingerprint}"
                        ),
                    )
                )

            _assert_batch_committed_state(
                repository,
                database_name=database_name,
                environment_name=environment_name,
                candidate_ids=window.candidate_ids,
            )
            completed = _utc()
            status = "APPLIED" if inserted else "REUSED"
            batch_content_fingerprint = _batch_digest(window.candidate_ids)
            batch_receipt_fingerprint = _batch_receipt_fingerprint(
                preview.fingerprint,
                window.batch_number,
                window.candidate_ids,
            )
            material = (
                f"{batch_receipt_fingerprint}|{submitter_actor_id}|{approver_actor_id}|{started}"
            )
            execution_id = "nnglarun:spatial:mr:" + sha256(material.encode("utf-8")).hexdigest()[:24]
            receipt = SpatialExecutionReceipt(
                execution_id=execution_id,
                plan_id=PLAN_ID,
                plan_version=PLAN_VERSION,
                fingerprint=batch_receipt_fingerprint,
                content_fingerprint=batch_content_fingerprint,
                database_name=database_name,
                environment_name=environment_name,
                runtime_mode=RUNTIME_MODE,
                repository_revision=repository_revision,
                source_sha256=source_sha,
                submitter_actor_id=submitter_actor_id,
                approver_actor_id=approver_actor_id,
                selected_count=window.selected_count,
                inserted_count=inserted,
                reused_count=reused,
                quarantined_count=0,
                failed_count=0,
                status=status,
                started_at=started,
                completed_at=completed,
                items=tuple(execution_items),
            )
            repository.persist_execution_receipt(receipt)

        results.append(
            BatchExecutionResult(
                batch_number=window.batch_number,
                selected_count=window.selected_count,
                inserted_count=inserted,
                reused_count=reused,
                status=status,
                execution_id=execution_id,
                candidate_ids=window.candidate_ids,
            )
        )

    return tuple(results)


__all__ = [
    "PLAN_ID",
    "PLAN_VERSION",
    "MigrationReadyExecutionError",
    "confirmation_token",
    "build_spatial_preview",
    "execute_spatial",
]
