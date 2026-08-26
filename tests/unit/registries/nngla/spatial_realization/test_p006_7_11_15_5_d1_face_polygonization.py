import math

from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_polygonization import (
    FabricDefectKind,
    build_atomic_face_set,
    source_fabric_diagnostics,
)
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope


def _sum(defects, kind):
    return sum(item.area_km2 for item in defects if item.kind is kind)


def test_delivery1_northgate_reproduces_live_material_seam_and_keeps_it_as_governed_face_evidence():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    defects = source_fabric_diagnostics(scope)
    assert math.isclose(_sum(defects, FabricDefectKind.PARENT_GAP), 1.1332812266937642, rel_tol=0, abs_tol=2e-9)
    assert math.isclose(_sum(defects, FabricDefectKind.SIBLING_OUTSIDE_PARENT), 5.784425051040006e-7, rel_tol=0, abs_tol=1e-12)
    material_gap = max((d for d in defects if d.kind is FabricDefectKind.PARENT_GAP), key=lambda d: d.area_km2)
    assert material_gap.residual_class == "MATERIAL_TOPOLOGY_FAILURE"
    assert set(material_gap.adjacent_subject_ids) == {"NG-ADM-000037", "NG-ADM-000038"}
    assert 2.5 < material_gap.effective_width_m < 2.8

    graph = build_shared_edge_graph(scope)
    faces = build_atomic_face_set(scope, graph)
    assert any(face.classification.value == "MATERIAL_UNASSIGNED" for face in faces.faces)
    assert faces.governed_face_ids


def test_delivery1_nyara_reproduces_regional_gap_as_parent_scope_evidence_not_city_context_only():
    scope = resolve_initial_fabric_scope(
        "NG-PLC-000258", material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED",)
    )
    defects = source_fabric_diagnostics(scope)
    assert math.isclose(_sum(defects, FabricDefectKind.PARENT_GAP), 16.394774466742803, rel_tol=0, abs_tol=2e-8)
    assert any(d.residual_class == "MATERIAL_TOPOLOGY_FAILURE" for d in defects if d.kind is FabricDefectKind.PARENT_GAP)
    faces = build_atomic_face_set(scope, build_shared_edge_graph(scope))
    assert any(face.classification.value in {"MATERIAL_UNASSIGNED", "AMBIGUOUS_PROVENANCE"} for face in faces.faces)


def test_delivery1_silvermere_source_district_fabric_reproduces_material_overshoot_before_reconstruction():
    scope = resolve_initial_fabric_scope("NG-PLC-000258")
    defects = source_fabric_diagnostics(scope)
    assert math.isclose(_sum(defects, FabricDefectKind.SIBLING_OUTSIDE_PARENT), 0.010038004612870964, rel_tol=0, abs_tol=2e-12)
    outside = max((d for d in defects if d.kind is FabricDefectKind.SIBLING_OUTSIDE_PARENT), key=lambda d: d.area_km2)
    assert outside.requires_governed_review is True
    assert set(outside.adjacent_subject_ids) == {"NG-ADM-000083", "NG-ADM-000087"}


def test_delivery1_face_set_hash_replays_identically():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    graph = build_shared_edge_graph(scope)
    first = build_atomic_face_set(scope, graph)
    second = build_atomic_face_set(scope, graph)
    assert first.face_set_sha256 == second.face_set_sha256
    assert [(f.face_id, f.geometry_sha256) for f in first.faces] == [(f.face_id, f.geometry_sha256) for f in second.faces]
