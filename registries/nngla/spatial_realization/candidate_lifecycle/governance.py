"""Governance binding for material Delivery-1 shared-face decisions."""
from __future__ import annotations

import re

from .contracts import CandidateRuntime, GovernedDecisionRecord
from .fingerprints import stable_id
from ..contracts import BoundaryConflictDecision, FaceAssignmentDecision

_SHA = re.compile(r"^[0-9a-f]{64}$")


class CandidateGovernanceError(RuntimeError):
    pass


def _reject_test_only(kind: str, reference: str, runtime_mode: CandidateRuntime) -> None:
    if runtime_mode is CandidateRuntime.PRODUCTION and (
        "TEST_ONLY" in kind.upper() or reference.upper().startswith("TEST-ONLY")
    ):
        raise CandidateGovernanceError("test-only governance evidence is prohibited in production candidate lifecycle")


def _validate_run_scope(fabric_run_id: str, scope_fingerprint: str) -> None:
    if not str(fabric_run_id).startswith("fabric-run:nngla:"):
        raise CandidateGovernanceError("governance decision requires exact fabric run identity")
    if _SHA.fullmatch(str(scope_fingerprint)) is None:
        raise CandidateGovernanceError("governance decision requires exact scope fingerprint")


def bind_governance_decisions(
    *,
    fabric_run_id: str,
    scope_fingerprint: str,
    face_decisions: tuple[FaceAssignmentDecision, ...] = (),
    boundary_decisions: tuple[BoundaryConflictDecision, ...] = (),
    reviewer_actor_id: str,
    approver_actor_id: str,
    runtime_mode: CandidateRuntime | str,
) -> tuple[GovernedDecisionRecord, ...]:
    """Bind each material decision to one exact run, scope and target geometry."""
    runtime = CandidateRuntime(runtime_mode)
    _validate_run_scope(fabric_run_id, scope_fingerprint)
    if not reviewer_actor_id or not approver_actor_id or reviewer_actor_id == approver_actor_id:
        raise CandidateGovernanceError("distinct reviewer and approver are required")
    records: list[GovernedDecisionRecord] = []
    for item in face_decisions:
        _reject_test_only(item.decision_kind.value, item.decision_reference, runtime)
        material = {
            "run": fabric_run_id, "scope": scope_fingerprint,
            "type": "FACE_ASSIGNMENT", "target": item.face_id, "geometry": item.face_geometry_sha256,
            "owner": item.owner_subject_id, "kind": item.decision_kind.value, "reference": item.decision_reference,
            "rationale": item.rationale, "reviewer": reviewer_actor_id, "approver": approver_actor_id,
            "runtime": runtime.value,
        }
        records.append(GovernedDecisionRecord(
            decision_id=stable_id("fabric-decision:nngla:", material),
            fabric_run_id=fabric_run_id, scope_fingerprint=scope_fingerprint,
            decision_type="FACE_ASSIGNMENT", target_id=item.face_id,
            target_geometry_sha256=item.face_geometry_sha256, owner_subject_id=item.owner_subject_id,
            decision_kind=item.decision_kind.value, decision_reference=item.decision_reference,
            rationale=item.rationale, reviewer_actor_id=reviewer_actor_id,
            approver_actor_id=approver_actor_id, runtime_mode=runtime,
        ))
    for item in boundary_decisions:
        _reject_test_only(item.decision_kind.value, item.decision_reference, runtime)
        material = {
            "run": fabric_run_id, "scope": scope_fingerprint,
            "type": "BOUNDARY_CONFLICT", "target": item.defect_id, "geometry": item.defect_geometry_sha256,
            "owner": "", "kind": item.decision_kind.value, "reference": item.decision_reference,
            "action": item.action, "rationale": item.rationale, "reviewer": reviewer_actor_id,
            "approver": approver_actor_id, "runtime": runtime.value,
        }
        records.append(GovernedDecisionRecord(
            decision_id=stable_id("fabric-decision:nngla:", material),
            fabric_run_id=fabric_run_id, scope_fingerprint=scope_fingerprint,
            decision_type="BOUNDARY_CONFLICT", target_id=item.defect_id,
            target_geometry_sha256=item.defect_geometry_sha256, owner_subject_id="",
            decision_kind=item.decision_kind.value, decision_reference=item.decision_reference,
            rationale=f"{item.action}: {item.rationale}", reviewer_actor_id=reviewer_actor_id,
            approver_actor_id=approver_actor_id, runtime_mode=runtime,
        ))
    return tuple(sorted(records, key=lambda row: row.decision_id))


__all__ = ["CandidateGovernanceError", "bind_governance_decisions"]
