import pytest

from registries.nngla.spatial_realization.contracts import (
    BoundaryConflictDecision,
    BoundaryConflictDecisionKind,
    FaceAssignmentDecision,
    FaceDecisionKind,
)
from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_assignment import FaceAssignmentError, assign_atomic_faces
from registries.nngla.spatial_realization.face_polygonization import FabricDefectKind, build_atomic_face_set
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope


def fixture_decisions(scope, face_set):
    face_decisions = []
    sibling_ids = [item.subject_id for item in scope.exhaustive_siblings]
    for face in face_set.faces:
        if face.automatically_owned:
            continue
        eligible = list(face.adjacent_subject_ids) or list(face.historical_owner_ids) or sibling_ids
        face_decisions.append(FaceAssignmentDecision(
            face_id=face.face_id,
            face_geometry_sha256=face.geometry_sha256,
            owner_subject_id=sorted(eligible)[0],
            decision_kind=FaceDecisionKind.TEST_ONLY_GOVERNANCE_FIXTURE,
            decision_reference="TEST-ONLY:" + face.face_id[-16:],
            rationale="Non-authoritative fixture proving topology convergence only.",
        ))
    boundary_decisions = []
    for defect in face_set.defects:
        if defect.kind is FabricDefectKind.SIBLING_OUTSIDE_PARENT and defect.requires_governed_review:
            boundary_decisions.append(BoundaryConflictDecision(
                defect_id=defect.defect_id,
                defect_geometry_sha256=defect.geometry_sha256,
                decision_kind=BoundaryConflictDecisionKind.TEST_ONLY_HIERARCHY_FIXTURE,
                decision_reference="TEST-ONLY:" + defect.defect_id[-16:],
                action="EXCLUDE_OUTSIDE_QUALIFIED_PARENT",
                rationale="Non-authoritative hierarchy fixture; qualified parent envelope controls the prototype candidate.",
            ))
    return tuple(face_decisions), tuple(boundary_decisions)


def test_delivery1_material_northgate_face_cannot_be_assigned_without_explicit_governed_decision():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    face_set = build_atomic_face_set(scope, build_shared_edge_graph(scope))
    _, boundary_decisions = fixture_decisions(scope, face_set)
    with pytest.raises(FaceAssignmentError, match="governed face"):
        assign_atomic_faces(scope, face_set, boundary_conflict_decisions=boundary_decisions)


def test_delivery1_explicit_test_only_governance_fixture_can_assign_complete_northgate_face_set_without_nearest_seed_logic():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    face_set = build_atomic_face_set(scope, build_shared_edge_graph(scope))
    faces, boundaries = fixture_decisions(scope, face_set)
    result = assign_atomic_faces(scope, face_set, face_decisions=faces, boundary_conflict_decisions=boundaries)
    assert len(result.sibling_candidates) == 8
    assert len(result.assigned_faces) == len(face_set.faces)
    assert len(result.assignment_sha256) == 64
    assert all(candidate.assigned_face_ids for candidate in result.sibling_candidates)


def test_delivery1_silvermere_material_parent_overshoot_requires_explicit_parent_envelope_decision():
    scope = resolve_initial_fabric_scope("NG-PLC-000258")
    face_set = build_atomic_face_set(scope, build_shared_edge_graph(scope))
    faces, boundaries = fixture_decisions(scope, face_set)
    assert boundaries
    with pytest.raises(FaceAssignmentError, match="parent-boundary conflict"):
        assign_atomic_faces(scope, face_set, face_decisions=faces)
    result = assign_atomic_faces(scope, face_set, face_decisions=faces, boundary_conflict_decisions=boundaries)
    assert len(result.sibling_candidates) == 8
    assert result.boundary_conflict_decision_refs


def test_delivery1_assignment_module_contains_no_voronoi_or_nearest_seed_material_owner():
    from pathlib import Path
    body = Path("registries/nngla/spatial_realization/face_assignment.py").read_text()
    assert "ST_VoronoiPolygons" not in body
    assert "nearest_seed(" not in body
