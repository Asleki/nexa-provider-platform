"""Governed atomic-face assignment for Delivery-1 shared-face recovery.

Unique historical ownership may be preserved automatically.  Every other face
requires an explicit decision bound to the face geometry hash.  Material faces
are never assigned from nearest-seed or Voronoi proximity in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping

from .contracts import (
    BoundaryConflictDecision,
    FaceAssignmentDecision,
    FaceDecisionKind,
    ParentFabricScope,
)
from .face_polygonization import FabricDefectKind, FabricFaceSet


class FaceAssignmentError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AssignedFace:
    face_id: str
    geometry_sha256: str
    owner_subject_id: str
    decision_kind: str
    decision_reference: str


@dataclass(frozen=True, slots=True)
class SiblingFabricCandidate:
    subject_id: str
    candidate_id: str
    geometry_sha256: str
    geometry_wkb_hex: str
    assigned_face_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FabricAssignmentResult:
    scope_fingerprint: str
    face_set_sha256: str
    assignment_sha256: str
    assigned_faces: tuple[AssignedFace, ...]
    sibling_candidates: tuple[SiblingFabricCandidate, ...]
    boundary_conflict_decision_refs: tuple[str, ...]

    @property
    def candidate_by_subject(self):
        return {item.subject_id: item for item in self.sibling_candidates}


def _wkb_hash(geometry) -> str:
    from shapely import normalize, to_wkb
    normalized = normalize(geometry)
    return sha256(to_wkb(normalized, hex=False, byte_order=1)).hexdigest()


def assign_atomic_faces(
    scope: ParentFabricScope,
    face_set: FabricFaceSet,
    *,
    face_decisions: Iterable[FaceAssignmentDecision] = (),
    boundary_conflict_decisions: Iterable[BoundaryConflictDecision] = (),
    geometry_overrides: Mapping[str, object] | None = None,
) -> FabricAssignmentResult:
    if face_set.scope_fingerprint != scope.fingerprint:
        raise FaceAssignmentError("face set/scope fingerprint mismatch")
    sibling_ids = {item.subject_id for item in scope.exhaustive_siblings}
    face_decisions = tuple(face_decisions)
    boundary_conflict_decisions = tuple(boundary_conflict_decisions)
    face_decision_map = {item.face_id: item for item in face_decisions}
    if len(face_decision_map) != len(face_decisions):
        raise FaceAssignmentError("duplicate face decision identity")
    boundary_map = {item.defect_id: item for item in boundary_conflict_decisions}
    if len(boundary_map) != len(boundary_conflict_decisions):
        raise FaceAssignmentError("duplicate boundary conflict decision identity")

    required_outside = [
        defect for defect in face_set.defects
        if defect.kind in {
            FabricDefectKind.SIBLING_OUTSIDE_PARENT,
            FabricDefectKind.INDIVIDUAL_SIBLING_OUTSIDE_PARENT,
        } and defect.requires_governed_review
    ]
    for defect in required_outside:
        decision = boundary_map.get(defect.defect_id)
        if decision is None:
            raise FaceAssignmentError("material parent-boundary conflict lacks explicit decision: " + defect.defect_id)
        if decision.defect_geometry_sha256 != defect.geometry_sha256:
            raise FaceAssignmentError("boundary conflict decision geometry hash mismatch")
        if decision.action != "EXCLUDE_OUTSIDE_QUALIFIED_PARENT":
            raise FaceAssignmentError("Delivery-1 candidate fabric requires explicit parent-envelope exclusion decision")

    from shapely import from_geojson, from_wkb, normalize, to_wkb
    from shapely.ops import unary_union

    assigned = []
    owner_geometries = {subject_id: [] for subject_id in sibling_ids}
    owner_faces = {subject_id: [] for subject_id in sibling_ids}

    for face in face_set.faces:
        if face.automatically_owned:
            owner = face.historical_owner_ids[0]
            decision_kind = FaceDecisionKind.PRESERVE_UNIQUE.value
            decision_reference = "SOURCE_UNIQUE_COVERAGE"
        else:
            decision = face_decision_map.get(face.face_id)
            if decision is None:
                raise FaceAssignmentError("governed face lacks explicit decision: " + face.face_id)
            if decision.face_geometry_sha256 != face.geometry_sha256:
                raise FaceAssignmentError("face decision geometry hash mismatch: " + face.face_id)
            if decision.owner_subject_id not in sibling_ids:
                raise FaceAssignmentError("face decision owner is outside exhaustive sibling set")
            if decision.decision_kind is FaceDecisionKind.PRESERVE_UNIQUE:
                raise FaceAssignmentError("non-unique face cannot use PRESERVE_UNIQUE decision")
            owner = decision.owner_subject_id
            decision_kind = decision.decision_kind.value
            decision_reference = decision.decision_reference
        if owner not in sibling_ids:
            raise FaceAssignmentError("assigned owner is outside exhaustive sibling set")
        geometry = from_wkb(bytes.fromhex(face.geometry_wkb_hex))
        owner_geometries[owner].append(geometry)
        owner_faces[owner].append(face.face_id)
        assigned.append(AssignedFace(
            face_id=face.face_id,
            geometry_sha256=face.geometry_sha256,
            owner_subject_id=owner,
            decision_kind=decision_kind,
            decision_reference=decision_reference,
        ))

    # Candidate geometry is a pure dissolve of the common atomic face set.
    # Parent-boundary conflicts remain explicit evidence/decisions; Delivery-1
    # deliberately avoids a second independent clipping pass here.

    candidates = []
    for subject_id in sorted(sibling_ids):
        geometries = owner_geometries[subject_id]
        if not geometries:
            raise FaceAssignmentError("exhaustive sibling has no assigned face: " + subject_id)
        candidate_geometry = normalize(unary_union(geometries))
        digest = _wkb_hash(candidate_geometry)
        candidates.append(SiblingFabricCandidate(
            subject_id=subject_id,
            candidate_id="fabric-candidate:nngla:" + sha256(
                f"{scope.fingerprint}|{face_set.face_set_sha256}|{subject_id}|{digest}".encode()
            ).hexdigest(),
            geometry_sha256=digest,
            geometry_wkb_hex=to_wkb(candidate_geometry, hex=True, byte_order=1),
            assigned_face_ids=tuple(sorted(owner_faces[subject_id])),
        ))

    assigned = tuple(sorted(assigned, key=lambda item: item.face_id))
    candidates = tuple(sorted(candidates, key=lambda item: item.subject_id))
    boundary_refs = tuple(sorted(boundary_map[item.defect_id].decision_reference for item in required_outside))
    material = {
        "scope": scope.fingerprint,
        "face_set": face_set.face_set_sha256,
        "assigned": [
            (item.face_id, item.geometry_sha256, item.owner_subject_id, item.decision_kind, item.decision_reference)
            for item in assigned
        ],
        "candidates": [
            (item.subject_id, item.geometry_sha256, item.assigned_face_ids)
            for item in candidates
        ],
        "boundary_conflicts": boundary_refs,
    }
    assignment_sha = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return FabricAssignmentResult(
        scope_fingerprint=scope.fingerprint,
        face_set_sha256=face_set.face_set_sha256,
        assignment_sha256=assignment_sha,
        assigned_faces=assigned,
        sibling_candidates=candidates,
        boundary_conflict_decision_refs=boundary_refs,
    )


__all__ = [
    "FaceAssignmentError",
    "AssignedFace",
    "SiblingFabricCandidate",
    "FabricAssignmentResult",
    "assign_atomic_faces",
]
