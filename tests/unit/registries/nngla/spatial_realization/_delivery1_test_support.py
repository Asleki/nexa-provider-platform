"""Test-only governance fixtures for Delivery-1 topology-convergence proofs.

These helpers deliberately choose an owner only inside the test harness.  They
are not authority policy and must never be imported by production code.
"""
from registries.nngla.spatial_realization.contracts import (
    BoundaryConflictDecision,
    BoundaryConflictDecisionKind,
    FaceAssignmentDecision,
    FaceDecisionKind,
)
from registries.nngla.spatial_realization.face_polygonization import FabricDefectKind


def governance_fixture_decisions(scope, face_set):
    sibling_ids = tuple(sorted(item.subject_id for item in scope.exhaustive_siblings))
    face_decisions = []
    for face in face_set.faces:
        if face.automatically_owned:
            continue
        eligible = tuple(sorted(set(face.adjacent_subject_ids or face.historical_owner_ids or sibling_ids)))
        owner = next((value for value in eligible if value in sibling_ids), sibling_ids[0])
        face_decisions.append(FaceAssignmentDecision(
            face_id=face.face_id,
            face_geometry_sha256=face.geometry_sha256,
            owner_subject_id=owner,
            decision_kind=FaceDecisionKind.TEST_ONLY_GOVERNANCE_FIXTURE,
            decision_reference="TEST-ONLY-FACE:" + face.face_id[-20:],
            rationale=(
                "Non-authoritative test fixture. It exists only to prove that the shared-face "
                "topology converges once an explicit face decision is supplied."
            ),
        ))

    boundary_decisions = []
    governed_boundary_kinds = {
        FabricDefectKind.SIBLING_OUTSIDE_PARENT,
        FabricDefectKind.INDIVIDUAL_SIBLING_OUTSIDE_PARENT,
    }
    for defect in face_set.defects:
        if defect.kind not in governed_boundary_kinds or not defect.requires_governed_review:
            continue
        boundary_decisions.append(BoundaryConflictDecision(
            defect_id=defect.defect_id,
            defect_geometry_sha256=defect.geometry_sha256,
            decision_kind=BoundaryConflictDecisionKind.TEST_ONLY_HIERARCHY_FIXTURE,
            decision_reference="TEST-ONLY-BOUNDARY:" + defect.defect_id[-20:],
            action="EXCLUDE_OUTSIDE_QUALIFIED_PARENT",
            rationale=(
                "Non-authoritative hierarchy fixture. It proves only that a qualified higher-tier "
                "parent envelope can constrain the read-only candidate fabric."
            ),
        ))
    return tuple(face_decisions), tuple(boundary_decisions)
