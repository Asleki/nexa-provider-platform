import math

from shapely import from_wkb

from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_assignment import assign_atomic_faces
from registries.nngla.spatial_realization.face_polygonization import (
    FabricDefectKind,
    build_atomic_face_set,
    source_fabric_diagnostics,
)
from registries.nngla.spatial_realization.fabric_qualification import qualify_candidate_fabric
from registries.nngla.spatial_realization.fabric_scope import (
    build_recursive_child_scope,
    resolve_initial_fabric_scope,
)

from _delivery1_test_support import governance_fixture_decisions


def _build_candidate(scope, overrides=None):
    graph = build_shared_edge_graph(scope, geometry_overrides=overrides)
    faces = build_atomic_face_set(scope, graph, geometry_overrides=overrides)
    face_decisions, boundary_decisions = governance_fixture_decisions(scope, faces)
    assignment = assign_atomic_faces(
        scope,
        faces,
        face_decisions=face_decisions,
        boundary_conflict_decisions=boundary_decisions,
        geometry_overrides=overrides,
    )
    qualification = qualify_candidate_fabric(scope, faces, assignment, geometry_overrides=overrides)
    return graph, faces, assignment, qualification


def test_delivery1_nyara_silvermere_golden_is_region_first_and_binds_child_run_to_exact_parent_candidate():
    region_scope = resolve_initial_fabric_scope(
        "NG-PLC-000258",
        material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED", "CITY_DISTRICT_OVERSHOOT"),
    )
    assert region_scope.parent.subject_id == "NG-ADM-000004"
    assert [item.subject_id for item in region_scope.exhaustive_siblings] == [
        "NG-ADM-000078", "NG-ADM-000079", "NG-ADM-000080", "NG-ADM-000081",
    ]

    source_defects = source_fabric_diagnostics(region_scope)
    silvermere_parent_conflicts = [
        d for d in source_defects
        if d.kind is FabricDefectKind.INDIVIDUAL_SIBLING_OUTSIDE_PARENT
        and d.source_subject_ids == ("NG-ADM-000078",)
    ]
    assert math.isclose(sum(d.area_km2 for d in silvermere_parent_conflicts), 0.03340777276111234, rel_tol=0, abs_tol=2e-9)
    assert all(d.requires_governed_review for d in silvermere_parent_conflicts)

    regional_gaps = [d for d in source_defects if d.kind is FabricDefectKind.PARENT_GAP]
    assert math.isclose(sum(d.area_km2 for d in regional_gaps), 16.394774466742803, rel_tol=0, abs_tol=2e-8)

    _, region_faces, region_assignment, region_qualification = _build_candidate(region_scope)
    assert region_qualification.prototype_ready is True
    assert region_qualification.candidate_gap_km2 == 0.0
    assert region_qualification.candidate_outside_parent_km2 == 0.0
    assert region_qualification.candidate_positive_overlap_km2 == 0.0

    silvermere_parent_candidate = region_assignment.candidate_by_subject["NG-ADM-000078"]
    silvermere_parent_geometry = from_wkb(bytes.fromhex(silvermere_parent_candidate.geometry_wkb_hex))
    child_scope = build_recursive_child_scope(
        region_scope,
        "NG-ADM-000078",
        qualified_parent_geometry_sha256=silvermere_parent_candidate.geometry_sha256,
        qualified_parent_candidate_id=silvermere_parent_candidate.candidate_id,
    )
    assert child_scope.parent.geometry_checksum_sha256 == silvermere_parent_candidate.geometry_sha256
    assert child_scope.parent.source_candidate_id == silvermere_parent_candidate.candidate_id
    assert child_scope.parent.source_path_reference == f"derived-from:{region_scope.scope_id}"
    assert [item.subject_id for item in child_scope.overlays] == ["NG-ADM-000099"]

    overrides = {"NG-ADM-000078": silvermere_parent_geometry}
    _, child_faces, child_assignment, child_qualification = _build_candidate(child_scope, overrides)
    assert child_qualification.prototype_ready is True
    assert child_qualification.candidate_gap_km2 == 0.0
    assert child_qualification.candidate_outside_parent_km2 == 0.0
    assert child_qualification.candidate_positive_overlap_km2 == 0.0
    assert child_qualification.shared_face_identity_by_construction is True
    assert len(child_assignment.sibling_candidates) == 8

    # The frozen source city-district fabric still reproduces the supplied
    # material union overshoot before the qualified region-level parent is used.
    frozen_city_scope = resolve_initial_fabric_scope("NG-PLC-000258")
    frozen_defects = source_fabric_diagnostics(frozen_city_scope)
    union_overshoot = [d for d in frozen_defects if d.kind is FabricDefectKind.SIBLING_OUTSIDE_PARENT]
    assert math.isclose(sum(d.area_km2 for d in union_overshoot), 0.010038004612870964, rel_tol=0, abs_tol=2e-12)
    assert any(d.requires_governed_review for d in union_overshoot)
