"""Bundle 17E governed confirmation and fail-closed spatial execution."""
from __future__ import annotations

from datetime import datetime, timezone

from ._shared import (
    BASE_REPOSITORY_REVISION,
    COORDINATE_CANDIDATES_PATH,
    RUNTIME_MODE,
    sha256_path,
    stable_id,
)
from .batch import build_spatial_preview
from .canonical import canonical_by_candidate
from .contracts import SpatialExecutionItem, SpatialExecutionReceipt, SpatialMigrationAction, SpatialBatchPreview
from .geometry import geometry_by_candidate


class SpatialExecutionBlocked(RuntimeError):
    pass


class StaleSpatialPreviewError(SpatialExecutionBlocked):
    pass


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_spatial_batch(
    repository,
    preview: SpatialBatchPreview,
    *,
    confirmation_fingerprint: str,
    submitter_actor_id: str,
    approver_actor_id: str,
    repository_revision: str = BASE_REPOSITORY_REVISION,
) -> SpatialExecutionReceipt:
    if not submitter_actor_id or not approver_actor_id:
        raise SpatialExecutionBlocked("submitter and approver are required")
    if submitter_actor_id == approver_actor_id:
        raise SpatialExecutionBlocked("submitter and approver must remain separate")
    if confirmation_fingerprint != preview.fingerprint:
        raise SpatialExecutionBlocked("confirmation fingerprint does not match preview")

    current_target = repository.snapshot()
    current_preview = build_spatial_preview(current_target, repository_revision=repository_revision)
    if current_preview.fingerprint != preview.fingerprint:
        raise StaleSpatialPreviewError("target state or source selection changed after preview")
    if not current_preview.execution_ready:
        raise SpatialExecutionBlocked("spatial batch is not execution-ready; fail closed")
    if current_preview.quarantined_count:
        raise SpatialExecutionBlocked("spatial batch contains quarantined rows; no partial canonical import")

    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    started = _utc()
    items: list[SpatialExecutionItem] = []
    inserted = reused = 0
    with repository.transaction():
        if hasattr(repository, "ensure_source_contract"):
            repository.ensure_source_contract(
                sha256_path(COORDINATE_CANDIDATES_PATH),
                "data/novegeo/nngla/spatial-fabric/source/05_spatial_candidates/novegeo_coordinate_candidates_v002.csv",
                current_preview.selected_count,
                COORDINATE_CANDIDATES_PATH.stat().st_size,
            )
        for item in current_preview.items:
            if item.migration_action is SpatialMigrationAction.INSERT_NEW:
                outcome = repository.persist_point(
                    crosswalks[item.coordinate_candidate_id],
                    geometries[item.coordinate_candidate_id],
                )
                if outcome == "INSERTED":
                    inserted += 1
                else:
                    reused += 1
            elif item.migration_action is SpatialMigrationAction.REUSE_CANONICAL:
                outcome = "REUSED"
                reused += 1
            else:
                raise SpatialExecutionBlocked(f"unexpected execution action {item.migration_action.value}")
            items.append(SpatialExecutionItem(
                coordinate_candidate_id=item.coordinate_candidate_id,
                canonical_spatial_point_id=item.canonical_spatial_point_id,
                geometry_id=item.geometry_id,
                outcome=outcome,
            ))

        completed = _utc()
        status = "APPLIED" if inserted else "REUSED"
        execution_id = stable_id(
            "nnglarun:spatial:", current_preview.fingerprint, submitter_actor_id, approver_actor_id, status
        )
        receipt = SpatialExecutionReceipt(
            execution_id=execution_id,
            plan_id="P006.7.11.7.7-8-BUNDLE17E",
            plan_version=1,
            fingerprint=current_preview.fingerprint,
            content_fingerprint=current_preview.content_fingerprint,
            database_name=current_preview.database_name,
            environment_name=current_preview.environment_name,
            runtime_mode=RUNTIME_MODE,
            repository_revision=repository_revision,
            source_sha256=current_preview.source_sha256,
            submitter_actor_id=submitter_actor_id,
            approver_actor_id=approver_actor_id,
            selected_count=current_preview.selected_count,
            inserted_count=inserted,
            reused_count=reused,
            quarantined_count=0,
            failed_count=0,
            status=status,
            started_at=started,
            completed_at=completed,
            items=tuple(items),
        )
        repository.persist_execution_receipt(receipt)
    return receipt


__all__ = ["SpatialExecutionBlocked", "StaleSpatialPreviewError", "execute_spatial_batch"]
