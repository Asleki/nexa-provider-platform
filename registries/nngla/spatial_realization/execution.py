"""Atomic governed execution for approved spatial-realization previews."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

from .contracts import (
    GeometryRole,
    ReconciliationAction,
    SpatialRealizationExecutionReceipt,
)
from .preview import build_preview, confirmation_token


class SpatialRealizationExecutionError(RuntimeError):
    pass


def _candidate_index(preview):
    out={}
    for assessment in preview.assessments:
        for candidate in assessment.candidates:
            out[(candidate.root_place_id,candidate.subject_id,candidate.geometry_role)]=candidate
    return out


def execute_preview(
    repository,
    topology_engine,
    *,
    root_ids,
    repository_revision: str,
    approved_fingerprint: str,
    confirmation: str,
    submitter_actor_id: str,
    approver_actor_id: str,
) -> SpatialRealizationExecutionReceipt:
    submitter=str(submitter_actor_id).strip();approver=str(approver_actor_id).strip()
    if not submitter or not approver or submitter==approver:
        raise ValueError("distinct submitter and approver are required")
    from .selection import normalize_city_root_ids
    normalized=normalize_city_root_ids(root_ids)
    approved=str(approved_fingerprint).strip()
    replay=repository.replay(approved,normalized)
    if replay is not None:
        if confirmation != confirmation_token(replay.database_name, approved):
            raise SpatialRealizationExecutionError("NNGLA spatial realization confirmation token does not match")
        current=build_preview(repository,topology_engine,root_ids=normalized,repository_revision=repository_revision)
        if not current.execution_ready or any(item.action not in {ReconciliationAction.REUSE_EXISTING,ReconciliationAction.NO_CHANGE} for item in current.reconciliation):
            raise SpatialRealizationExecutionError("previously executed selection no longer matches current governed state")
        repository.verify_applied(current)
        return replace(replay,status="REUSED",replayed=True)

    preview=build_preview(repository,topology_engine,root_ids=normalized,repository_revision=repository_revision)
    if preview.fingerprint!=approved:
        raise SpatialRealizationExecutionError("approved preview fingerprint is stale or does not match target")
    if confirmation!=confirmation_token(preview.database_name,preview.fingerprint):
        raise SpatialRealizationExecutionError("NNGLA spatial realization confirmation token does not match")
    if not preview.execution_ready:
        codes=sorted({f.rule_code for f in preview.blocking_findings})
        reasons=sorted({item.reason for item in preview.blocked_actions})
        raise SpatialRealizationExecutionError("spatial realization preview is blocked: "+",".join(codes+reasons))

    with repository.transaction():
        # Re-read target and recompute geometry-derived qualification *inside the
        # write transaction*.  A changed target or source plan invalidates the
        # operator-approved fingerprint before any NG-GEO allocation occurs.
        fresh=build_preview(repository,topology_engine,root_ids=preview.normalized_root_ids,repository_revision=repository_revision)
        if fresh.fingerprint!=preview.fingerprint:
            raise SpatialRealizationExecutionError("target changed after approval; fresh preview required")
        if not fresh.execution_ready:
            raise SpatialRealizationExecutionError("fresh in-transaction preview is no longer execution-ready")
        candidates=_candidate_index(fresh)
        closure_by_root={closure.root.place_id:closure for closure in fresh.closures}
        assessment_by_root={assessment.root_place_id:assessment for assessment in fresh.assessments}
        geometry_inserts=0;associations=0;reused=0;details=[]
        for item in fresh.reconciliation:
            action_id=f"spatial-action:{item.root_place_id}:{item.subject_id}:{item.geometry_role.value}"
            if item.action is ReconciliationAction.NO_CHANGE:
                details.append({"action_id":action_id,"root_place_id":item.root_place_id,"subject_id":item.subject_id,"geometry_role":item.geometry_role.value,"outcome":"NO_CHANGE","association_applied":False,"reason":item.reason,"repair_mode":fresh.repair_mode,"effective_date":fresh.effective_date})
                continue
            if item.action is ReconciliationAction.BLOCKED:
                raise SpatialRealizationExecutionError("blocked reconciliation item reached execution: "+action_id)
            key=(item.root_place_id,item.subject_id,item.geometry_role)
            candidate=candidates.get(key)
            if candidate is None:
                raise SpatialRealizationExecutionError("execution candidate missing for "+action_id)
            geometry_id=item.existing_geometry_id
            association_applied=False
            if item.action is ReconciliationAction.CREATE_NEW:
                geometry_id=repository.reserve_geometry(candidate)
                repository.persist_geometry(candidate,geometry_id)
                geometry_inserts+=1
                if candidate.geometry_role in {GeometryRole.PLACE_REFERENCE_POINT,GeometryRole.ADMINISTRATIVE_BOUNDARY}:
                    repository.associate(candidate,geometry_id);associations+=1;association_applied=True
                outcome="CREATED"
            elif item.action is ReconciliationAction.ASSOCIATE_EXISTING:
                if not geometry_id:raise SpatialRealizationExecutionError("ASSOCIATE_EXISTING has no geometry identity")
                repository.associate(candidate,geometry_id);associations+=1;association_applied=True;outcome="ASSOCIATED"
            elif item.action is ReconciliationAction.CREATE_SUCCESSOR:
                if not geometry_id:raise SpatialRealizationExecutionError("CREATE_SUCCESSOR has no predecessor geometry")
                successor_id=repository.reserve_geometry(candidate)
                repository.supersede(candidate,successor_id,geometry_id)
                geometry_id=successor_id;geometry_inserts+=1
                if candidate.geometry_role in {GeometryRole.PLACE_REFERENCE_POINT,GeometryRole.ADMINISTRATIVE_BOUNDARY}:associations+=1;association_applied=True
                outcome="SUPERSEDED"
            elif item.action is ReconciliationAction.REUSE_EXISTING:
                reused+=1;outcome="REUSED"
            else:
                raise SpatialRealizationExecutionError("unsupported realization action: "+item.action.value)
            closure=closure_by_root[item.root_place_id]
            details.append({
                "action_id":action_id,"root_place_id":item.root_place_id,"subject_id":item.subject_id,
                "subject_type":item.subject_type.value,"geometry_role":item.geometry_role.value,"outcome":outcome,
                "geometry_id":geometry_id,"candidate_checksum":item.candidate_checksum,"source_candidate_id":item.source_candidate_id,
                "predecessor_source_candidate_id":candidate.predecessor_source_candidate_id,
                "repair_policy_id":candidate.repair_policy_id,
                "source_finding_ids":[f.finding_id for f in assessment_by_root[item.root_place_id].findings if f.subject_id==item.subject_id and f.assessment_stage.value=="SOURCE_CANDIDATE"],
                "successor_finding_ids":[f.finding_id for f in assessment_by_root[item.root_place_id].findings if f.subject_id==item.subject_id and f.assessment_stage.value=="SUCCESSOR_CANDIDATE"],
                "supporting_spatial_point_id":closure.supporting_spatial_point_id if item.geometry_role is GeometryRole.PLACE_REFERENCE_POINT else "",
                "repair_mode":fresh.repair_mode,
                "effective_date":fresh.effective_date,
                "association_applied":association_applied,"publication_ready":False,"reason":item.reason,
            })
        repository.verify_applied(fresh)
        execution_id="nnglarun:spatial-realization:"+fresh.fingerprint[:32]
        receipt=SpatialRealizationExecutionReceipt(
            execution_id=execution_id,fingerprint_sha256=fresh.fingerprint,database_name=fresh.database_name,
            environment_name=fresh.environment_name,repository_revision=fresh.repository_revision,
            submitter_actor_id=submitter,approver_actor_id=approver,selected_root_count=len(fresh.normalized_root_ids),
            geometry_insert_count=geometry_inserts,association_count=associations,reused_count=reused,status="APPLIED",replayed=False,
        )
        repository.persist_receipt(receipt,tuple(details),fresh)
        return receipt


__all__=["SpatialRealizationExecutionError","execute_preview"]
