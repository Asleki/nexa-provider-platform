"""Build immutable candidate packages from the locked Delivery-1 preview graph."""
from __future__ import annotations

from dataclasses import replace

from .contracts import CandidateLifecycleStatus, CandidatePackage, CandidateRuntime, GovernedDecisionRecord
from .fingerprints import digest, stable_id
from ..shared_face_preview import SharedFacePrototypePreview


def _input_payload(item):
    return {
        "role": item.input_role.value, "subjectId": item.subject_id,
        "administrativeType": item.administrative_type_code, "canonicalName": item.canonical_name,
        "sourceCandidateId": item.source_candidate_id, "geometrySha256": item.geometry_checksum_sha256,
        "sourcePathReference": item.source_path_reference,
    }


def candidate_run_identity(
    preview: SharedFacePrototypePreview,
    *,
    runtime_mode: CandidateRuntime | str,
    parent_candidate_id: str = "",
    parent_candidate_geometry_sha256: str = "",
) -> tuple[str, dict[str, object]]:
    """Return the deterministic run identity before governance records are bound."""
    runtime = CandidateRuntime(runtime_mode)
    assignment_sha = preview.assignment.assignment_sha256 if preview.assignment is not None else ""
    run_material: dict[str, object] = {
        "scope": preview.scope.fingerprint,
        "input": preview.scope.input_digest,
        "runtimeSignature": preview.scope.runtime_signature.digest,
        "edgeGraph": preview.edge_graph.graph_sha256,
        "faceSet": preview.face_set.face_set_sha256,
        "assignment": assignment_sha,
        "parentCandidateId": parent_candidate_id,
        "parentCandidateGeometrySha256": parent_candidate_geometry_sha256,
        "runtime": runtime.value,
    }
    return stable_id("fabric-run:nngla:", run_material), run_material


def _validate_decision_bindings(
    preview: SharedFacePrototypePreview,
    *,
    run_id: str,
    runtime: CandidateRuntime,
    decisions: tuple[GovernedDecisionRecord, ...],
) -> None:
    targets = {face.face_id: face.geometry_sha256 for face in preview.face_set.faces}
    targets.update({defect.defect_id: defect.geometry_sha256 for defect in preview.face_set.defects})
    for decision in decisions:
        if decision.fabric_run_id != run_id or decision.scope_fingerprint != preview.scope.fingerprint:
            raise ValueError("governed decision is bound to a different fabric run or scope")
        if decision.runtime_mode is not runtime:
            raise ValueError("governed decision runtime does not match candidate package runtime")
        expected_geometry = targets.get(decision.target_id)
        if expected_geometry is None or expected_geometry != decision.target_geometry_sha256:
            raise ValueError("governed decision target geometry is not part of this candidate package")


def build_candidate_package(
    preview: SharedFacePrototypePreview,
    *,
    runtime_mode: CandidateRuntime | str,
    author_actor_id: str,
    decisions: tuple[GovernedDecisionRecord, ...] = (),
    parent_candidate_id: str = "",
    parent_candidate_geometry_sha256: str = "",
) -> CandidatePackage:
    runtime = CandidateRuntime(runtime_mode)
    scope = preview.scope
    inputs = tuple(_input_payload(item) for item in (scope.parent,) + scope.exhaustive_siblings + scope.overlays)
    edges = tuple({
        "edgeId": e.edge_id, "geometrySha256": e.geometry_sha256, "geometryWkbHex": e.geometry_wkb_hex,
        "lineage": tuple({"subjectId": row.subject_id, "sourceCandidateId": row.source_candidate_id, "inputRole": row.input_role} for row in e.lineage),
    } for e in preview.edge_graph.edges)
    faces = tuple({
        "faceId": f.face_id, "geometrySha256": f.geometry_sha256, "geometryWkbHex": f.geometry_wkb_hex,
        "classification": f.classification.value, "historicalOwnerIds": tuple(f.historical_owner_ids),
        "adjacentSubjectIds": tuple(f.adjacent_subject_ids), "sourceDefectIds": tuple(f.source_defect_ids),
    } for f in preview.face_set.faces)
    defects = tuple({
        "defectId": d.defect_id, "kind": d.kind.value, "geometrySha256": d.geometry_sha256,
        "geometryWkbHex": d.geometry_wkb_hex, "residualClass": d.residual_class,
        "requiresGovernedReview": d.requires_governed_review, "sourceSubjectIds": tuple(d.source_subject_ids),
    } for d in preview.face_set.defects)
    if preview.assignment is None:
        assignment_sha = ""
        qualification_sha = ""
        assignments = ()
        candidates = ()
        status = CandidateLifecycleStatus.GOVERNANCE_REQUIRED
    else:
        assignment_sha = preview.assignment.assignment_sha256
        qualification_sha = preview.qualification.qualification_sha256 if preview.qualification else ""
        assignments = tuple({
            "faceId": a.face_id, "geometrySha256": a.geometry_sha256,
            "ownerSubjectId": a.owner_subject_id, "decisionKind": a.decision_kind,
            "decisionReference": a.decision_reference,
        } for a in preview.assignment.assigned_faces)
        candidates = tuple({
            "subjectId": c.subject_id, "candidateId": c.candidate_id,
            "geometrySha256": c.geometry_sha256, "geometryWkbHex": c.geometry_wkb_hex,
            "assignedFaceIds": tuple(c.assigned_face_ids),
        } for c in preview.assignment.sibling_candidates)
        status = CandidateLifecycleStatus.READY_FOR_CANDIDATE_QUALIFICATION
    run_id, run_material = candidate_run_identity(
        preview,
        runtime_mode=runtime,
        parent_candidate_id=parent_candidate_id,
        parent_candidate_geometry_sha256=parent_candidate_geometry_sha256,
    )
    ordered_decisions = tuple(sorted(decisions, key=lambda row: row.decision_id))
    _validate_decision_bindings(preview, run_id=run_id, runtime=runtime, decisions=ordered_decisions)
    base = CandidatePackage(
        fabric_run_id=run_id, requested_root_place_id=scope.requested_root_place_id,
        parent_administrative_area_id=scope.parent.subject_id, fabric_level=scope.level.value,
        runtime_mode=runtime, scope_fingerprint=scope.fingerprint, input_digest=scope.input_digest,
        runtime_signature_digest=scope.runtime_signature.digest, edge_graph_sha256=preview.edge_graph.graph_sha256,
        face_set_sha256=preview.face_set.face_set_sha256, assignment_sha256=assignment_sha,
        qualification_sha256=qualification_sha, author_actor_id=author_actor_id, lifecycle_status=status,
        parent_candidate_id=parent_candidate_id, parent_candidate_geometry_sha256=parent_candidate_geometry_sha256,
        inputs=inputs, edges=edges, faces=faces, defects=defects, decisions=ordered_decisions,
        assignments=assignments, sibling_candidates=candidates,
    )
    material = {
        "run": run_material, "root": base.requested_root_place_id, "parent": base.parent_administrative_area_id,
        "level": base.fabric_level, "inputs": inputs, "edges": edges, "faces": faces, "defects": defects,
        "decisions": ordered_decisions, "assignments": assignments, "candidates": candidates, "author": author_actor_id,
        "status": status.value,
    }
    return replace(base, package_sha256=digest(material))


__all__ = ["build_candidate_package", "candidate_run_identity"]
