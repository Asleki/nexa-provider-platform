from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_polygonization import source_fabric_diagnostics
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope
from registries.nngla.spatial_realization.source import (
    city_root_by_id,
    place_point_candidate,
    reference_point_support,
)


def test_delivery1_orivane_preserves_canonical_identity_reference_point_and_overlay_semantics():
    root = city_root_by_id()["NG-PLC-000001"]
    point = place_point_candidate(root.place_id)
    assert root.source_place_code == "NGP-000001"
    assert root.canonical_name == "Orivane"
    assert reference_point_support(root.place_id) == "NG-SPT-000629"
    assert '"coordinates":[36.4,0.892533]' in point.payload

    scope = resolve_initial_fabric_scope(root.place_id)
    assert scope.parent.subject_id == root.administrative_area_id
    assert len(scope.exhaustive_siblings) == 8
    assert all(item.administrative_type_code == "CITY_DISTRICT" for item in scope.exhaustive_siblings)
    assert len(scope.overlays) == 1
    assert scope.overlays[0].administrative_type_code == "INDUSTRIAL_ZONE"
    assert scope.overlays[0].subject_id not in {item.subject_id for item in scope.exhaustive_siblings}

    # Orivane's known source residuals are microscopic only; Delivery-1 must not
    # manufacture a successor or convert them into a tolerance-based PASS.
    defects = source_fabric_diagnostics(scope)
    assert defects
    assert all(item.residual_class != "MATERIAL_TOPOLOGY_FAILURE" for item in defects)
    graph = build_shared_edge_graph(scope)
    assert scope.overlays[0].subject_id not in set(graph.source_subject_ids)
