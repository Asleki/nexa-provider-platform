"""Deterministic preview construction for selected city-root realization runs."""
from __future__ import annotations

from hashlib import sha256
import json

from .closure import build_selection_closure
from .contracts import SpatialRealizationPreview
from .reconciliation import reconcile_selection
from .selection import normalize_city_root_ids
from .source import aggregate_source_sha256
from .topology import REPAIR_POLICY_ID, TOPOLOGY_POLICY_ID

PLAN_ID = "p006.7.11.15.5-spatial-batch-realization"
PLAN_VERSION = 2


def _assessment_payload(assessment):
    return {
        "root": assessment.root_place_id,
        "repair_applied": assessment.repair_applied,
        "candidates": [
            {
                "subject": item.subject_id,
                "role": item.geometry_role.value,
                "candidate": item.source_candidate_id,
                "checksum": item.checksum_sha256,
                "predecessor": item.predecessor_source_candidate_id,
                "repair_policy": item.repair_policy_id,
            }
            for item in sorted(assessment.candidates,key=lambda c:(c.subject_id,c.geometry_role.value))
        ],
        "findings": [
            {
                "id": f.finding_id,
                "code": f.rule_code,
                "severity": f.severity.value,
                "status": f.status.value,
                "subject": f.subject_id,
                "related": f.related_subject_id,
                "actual": f.actual,
                "stage": f.assessment_stage.value,
                "raw_predicate_result": f.raw_predicate_result,
                "difference_dimension": f.difference_dimension,
                "area_km2": f.area_km2,
                "area_ratio": f.area_ratio,
                "residual_class": f.residual_class,
                "repair": f.repair_eligibility,
            }
            for f in sorted(assessment.findings,key=lambda x:(x.rule_code,x.subject_id,x.finding_id))
        ],
    }



def _closure_payload(closure):
    return {
        "root": closure.root.place_id,
        "source_place_code": closure.root.source_place_code,
        "admin_root": closure.root.administrative_area_id,
        "validation_parent": closure.root.validation_parent_id,
        "supporting_spatial_point": closure.supporting_spatial_point_id,
        "exhaustive_children": [item.subject_id for item in closure.exhaustive_children],
        "exhaustive_child_seeds": [
            (seed.subject_id,seed.source_place_code,seed.place_id,seed.longitude,seed.latitude)
            for seed in closure.exhaustive_child_seeds
        ],
        "overlays": [item.subject_id for item in closure.overlays],
        "regional_partition_peers": [item.subject_id for item in closure.regional_partition_peers],
    }

def _reconciliation_payload(items):
    return [
        {
            "root": item.root_place_id,
            "subject": item.subject_id,
            "subject_type": item.subject_type.value,
            "role": item.geometry_role.value,
            "candidate_checksum": item.candidate_checksum,
            "source_candidate": item.source_candidate_id,
            "action": item.action.value,
            "reason": item.reason,
            "existing_geometry": item.existing_geometry_id,
        }
        for item in sorted(items,key=lambda x:(x.root_place_id,x.subject_id,x.geometry_role.value,x.action.value))
    ]


def _fingerprint_payload(*,normalized,source_sha,repository_revision,snapshot,closures,assessments,reconciliation,repair_mode,effective_date):
    return {
        "plan_id":PLAN_ID,
        "plan_version":PLAN_VERSION,
        "normalized_root_ids":list(normalized),
        "source_sha256":source_sha,
        "repository_revision":repository_revision,
        "database_name":snapshot.database_name,
        "environment_name":snapshot.environment_name,
        "target_snapshot_digest":snapshot.digest,
        "topology_policy_id":TOPOLOGY_POLICY_ID,
        "repair_policy_id":REPAIR_POLICY_ID,
        "repair_mode":repair_mode,
        "effective_date":effective_date,
        "closures":[_closure_payload(item) for item in sorted(closures,key=lambda x:x.root.place_id)],
        "assessments":[_assessment_payload(item) for item in sorted(assessments,key=lambda x:x.root_place_id)],
        "reconciliation":_reconciliation_payload(reconciliation),
    }


def build_preview(repository,topology_engine,*,root_ids,repository_revision:str) -> SpatialRealizationPreview:
    revision=str(repository_revision).strip()
    if not revision:raise ValueError("repository_revision is required")
    normalized=normalize_city_root_ids(root_ids)
    closures=build_selection_closure(normalized)
    snapshot=repository.snapshot(closures)
    if not snapshot.available:raise RuntimeError("live target snapshot is unavailable")
    assessments=tuple(topology_engine.assess(closure) for closure in closures)
    reconciliation=reconcile_selection(closures,assessments,snapshot)
    source_sha=aggregate_source_sha256()
    repair_mode=getattr(topology_engine,"repair_mode","UNSPECIFIED")
    if hasattr(repair_mode,"value"):
        repair_mode=repair_mode.value
    repair_mode=str(repair_mode)
    effective_date=str(getattr(repository,"effective_date","")).strip()
    if not effective_date:
        raise ValueError("repository effective_date is required for governed spatial realization")
    payload=_fingerprint_payload(normalized=normalized,source_sha=source_sha,repository_revision=revision,snapshot=snapshot,closures=closures,assessments=assessments,reconciliation=reconciliation,repair_mode=repair_mode,effective_date=effective_date)
    fingerprint=sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return SpatialRealizationPreview(
        plan_id=PLAN_ID,
        plan_version=PLAN_VERSION,
        normalized_root_ids=normalized,
        source_sha256=source_sha,
        repository_revision=revision,
        database_name=snapshot.database_name,
        environment_name=snapshot.environment_name,
        target_snapshot_digest=snapshot.digest,
        topology_policy_id=TOPOLOGY_POLICY_ID,
        repair_policy_id=REPAIR_POLICY_ID,
        repair_mode=repair_mode,
        effective_date=effective_date,
        closures=closures,
        assessments=assessments,
        reconciliation=reconciliation,
        fingerprint=fingerprint,
    )


def confirmation_token(database_name:str,fingerprint:str)->str:
    return f"REALIZE-NNGLA-CITIES::{database_name}::{fingerprint}"


__all__=["PLAN_ID","PLAN_VERSION","build_preview","confirmation_token"]
