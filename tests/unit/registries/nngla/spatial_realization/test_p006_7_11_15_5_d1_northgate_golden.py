import math

from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_assignment import assign_atomic_faces
from registries.nngla.spatial_realization.face_polygonization import (
    FabricDefectKind,
    build_atomic_face_set,
    source_fabric_diagnostics,
)
from registries.nngla.spatial_realization.fabric_qualification import qualify_candidate_fabric
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope

from _delivery1_test_support import governance_fixture_decisions


def test_delivery1_northgate_golden_reproduces_long_material_seam_then_converges_only_after_explicit_decision():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    defects = source_fabric_diagnostics(scope)
    gaps = [d for d in defects if d.kind is FabricDefectKind.PARENT_GAP]
    material = max(gaps, key=lambda d: d.area_km2)

    assert math.isclose(material.area_km2, 1.1332812266937642, rel_tol=0, abs_tol=2e-9)
    assert material.residual_class == "MATERIAL_TOPOLOGY_FAILURE"
    assert set(material.adjacent_subject_ids) == {"NG-ADM-000037", "NG-ADM-000038"}
    assert 2.5 < material.effective_width_m < 2.8

    graph = build_shared_edge_graph(scope)
    face_set = build_atomic_face_set(scope, graph)
    assert face_set.governed_face_ids
    assert any(face.classification.value == "MATERIAL_UNASSIGNED" for face in face_set.faces)

    face_decisions, boundary_decisions = governance_fixture_decisions(scope, face_set)
    assignment = assign_atomic_faces(
        scope,
        face_set,
        face_decisions=face_decisions,
        boundary_conflict_decisions=boundary_decisions,
    )
    qualification = qualify_candidate_fabric(scope, face_set, assignment)

    assert qualification.prototype_ready is True
    assert qualification.candidate_gap_km2 == 0.0
    assert qualification.candidate_outside_parent_km2 == 0.0
    assert qualification.candidate_positive_overlap_km2 == 0.0
    assert qualification.face_exclusivity is True
    assert qualification.complete_sibling_set is True
    assert qualification.shared_face_identity_by_construction is True
    assert len(assignment.sibling_candidates) == 8
    assert any(item.decision_kind == "TEST_ONLY_GOVERNANCE_FIXTURE" for item in assignment.assigned_faces)
