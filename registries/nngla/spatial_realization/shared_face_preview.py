"""Read-only orchestration for Delivery-1 shared-face recovery prototypes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .contracts import BoundaryConflictDecision, FaceAssignmentDecision, ParentFabricScope
from .edge_graph import SharedEdgeGraph, build_shared_edge_graph
from .face_assignment import FabricAssignmentResult, FaceAssignmentError, assign_atomic_faces
from .face_polygonization import FabricFaceSet, build_atomic_face_set
from .fabric_qualification import PrototypeFabricQualification, qualify_candidate_fabric
from .fabric_scope import build_recursive_child_scope, resolve_initial_fabric_scope


@dataclass(frozen=True, slots=True)
class SharedFacePrototypePreview:
    scope: ParentFabricScope
    edge_graph: SharedEdgeGraph
    face_set: FabricFaceSet
    assignment: FabricAssignmentResult | None
    qualification: PrototypeFabricQualification | None
    status: str
    blocked_reason: str = ""

    @property
    def fingerprint(self) -> str:
        if self.qualification is not None:
            return self.qualification.qualification_sha256
        if self.assignment is not None:
            return self.assignment.assignment_sha256
        return self.face_set.face_set_sha256


def build_read_only_shared_face_preview(
    root_place_id: str,
    *,
    material_rule_codes: Iterable[str] = (),
    face_decisions: Iterable[FaceAssignmentDecision] = (),
    boundary_conflict_decisions: Iterable[BoundaryConflictDecision] = (),
    geometry_overrides: Mapping[str, object] | None = None,
) -> SharedFacePrototypePreview:
    scope = resolve_initial_fabric_scope(
        root_place_id,
        material_rule_codes=tuple(material_rule_codes),
    )
    graph = build_shared_edge_graph(scope, geometry_overrides=geometry_overrides)
    face_set = build_atomic_face_set(scope, graph, geometry_overrides=geometry_overrides)
    try:
        assignment = assign_atomic_faces(
            scope,
            face_set,
            face_decisions=tuple(face_decisions),
            boundary_conflict_decisions=tuple(boundary_conflict_decisions),
            geometry_overrides=geometry_overrides,
        )
    except FaceAssignmentError as exc:
        return SharedFacePrototypePreview(
            scope=scope,
            edge_graph=graph,
            face_set=face_set,
            assignment=None,
            qualification=None,
            status="GOVERNED_DECISION_REQUIRED",
            blocked_reason=str(exc),
        )
    qualification = qualify_candidate_fabric(
        scope,
        face_set,
        assignment,
        geometry_overrides=geometry_overrides,
    )
    return SharedFacePrototypePreview(
        scope=scope,
        edge_graph=graph,
        face_set=face_set,
        assignment=assignment,
        qualification=qualification,
        status=qualification.status,
    )


def build_recursive_read_only_shared_face_preview(
    parent_preview: SharedFacePrototypePreview,
    child_parent_administrative_area_id: str,
    *,
    face_decisions: Iterable[FaceAssignmentDecision] = (),
    boundary_conflict_decisions: Iterable[BoundaryConflictDecision] = (),
) -> SharedFacePrototypePreview:
    if parent_preview.qualification is None or not parent_preview.qualification.prototype_ready:
        raise ValueError("recursive child preview requires a prototype-ready parent candidate")
    if parent_preview.assignment is None:
        raise ValueError("recursive child preview requires parent assignment")
    candidate = parent_preview.assignment.candidate_by_subject.get(child_parent_administrative_area_id)
    if candidate is None:
        raise ValueError("requested recursive child is not a candidate in the parent fabric")
    from shapely import from_wkb
    parent_geometry = from_wkb(bytes.fromhex(candidate.geometry_wkb_hex))
    child_scope = build_recursive_child_scope(
        parent_preview.scope,
        child_parent_administrative_area_id,
        qualified_parent_geometry_sha256=candidate.geometry_sha256,
        qualified_parent_candidate_id=candidate.candidate_id,
    )
    overrides = {child_parent_administrative_area_id: parent_geometry}
    graph = build_shared_edge_graph(child_scope, geometry_overrides=overrides)
    face_set = build_atomic_face_set(child_scope, graph, geometry_overrides=overrides)
    try:
        assignment = assign_atomic_faces(
            child_scope,
            face_set,
            face_decisions=tuple(face_decisions),
            boundary_conflict_decisions=tuple(boundary_conflict_decisions),
            geometry_overrides=overrides,
        )
    except FaceAssignmentError as exc:
        return SharedFacePrototypePreview(
            scope=child_scope,
            edge_graph=graph,
            face_set=face_set,
            assignment=None,
            qualification=None,
            status="GOVERNED_DECISION_REQUIRED",
            blocked_reason=str(exc),
        )
    qualification = qualify_candidate_fabric(
        child_scope,
        face_set,
        assignment,
        geometry_overrides=overrides,
    )
    return SharedFacePrototypePreview(
        scope=child_scope,
        edge_graph=graph,
        face_set=face_set,
        assignment=assignment,
        qualification=qualification,
        status=qualification.status,
    )


def preview_payload(preview: SharedFacePrototypePreview) -> dict[str, object]:
    qualification = preview.qualification
    return {
        "delivery": "P006.7.11.15.5-DELIVERY1-READ_ONLY_SHARED_FACE",
        "status": preview.status,
        "blockedReason": preview.blocked_reason or None,
        "fingerprint": preview.fingerprint,
        "scope": {
            "scopeId": preview.scope.scope_id,
            "scopeFingerprint": preview.scope.fingerprint,
            "requestedRootPlaceId": preview.scope.requested_root_place_id,
            "parentAdministrativeAreaId": preview.scope.parent.subject_id,
            "level": preview.scope.level.value,
            "exhaustiveSiblingIds": [item.subject_id for item in preview.scope.exhaustive_siblings],
            "overlayIds": [item.subject_id for item in preview.scope.overlays],
            "inputDigest": preview.scope.input_digest,
            "runtimeSignatureDigest": preview.scope.runtime_signature.digest,
        },
        "edgeGraph": {
            "sha256": preview.edge_graph.graph_sha256,
            "edgeCount": preview.edge_graph.edge_count,
        },
        "faces": {
            "faceSetSha256": preview.face_set.face_set_sha256,
            "count": len(preview.face_set.faces),
            "governedFaceIds": list(preview.face_set.governed_face_ids),
            "materialDefects": [
                {
                    "defectId": defect.defect_id,
                    "kind": defect.kind.value,
                    "areaKm2": defect.area_km2,
                    "effectiveWidthM": defect.effective_width_m,
                    "adjacentSubjectIds": list(defect.adjacent_subject_ids),
                    "sourceSubjectIds": list(defect.source_subject_ids),
                    "residualClass": defect.residual_class,
                }
                for defect in preview.face_set.material_defects
            ],
        },
        "assignment": None if preview.assignment is None else {
            "sha256": preview.assignment.assignment_sha256,
            "assignedFaceCount": len(preview.assignment.assigned_faces),
            "candidateCount": len(preview.assignment.sibling_candidates),
            "candidateHashes": {
                item.subject_id: item.geometry_sha256 for item in preview.assignment.sibling_candidates
            },
        },
        "qualification": None if qualification is None else {
            "sha256": qualification.qualification_sha256,
            "status": qualification.status,
            "prototypeReady": qualification.prototype_ready,
            "faceExclusivity": qualification.face_exclusivity,
            "completeSiblingSet": qualification.complete_sibling_set,
            "sharedFaceIdentityByConstruction": qualification.shared_face_identity_by_construction,
            "candidateGapKm2": qualification.candidate_gap_km2,
            "candidateOutsideParentKm2": qualification.candidate_outside_parent_km2,
            "unionOutsideParentDiagnosticKm2": qualification.union_outside_parent_diagnostic_km2,
            "candidatePositiveOverlapKm2": qualification.candidate_positive_overlap_km2,
        },
        "writeCapability": "NONE",
        "canonicalDatabaseMutation": False,
    }


__all__ = [
    "SharedFacePrototypePreview",
    "build_read_only_shared_face_preview",
    "build_recursive_read_only_shared_face_preview",
    "preview_payload",
]
