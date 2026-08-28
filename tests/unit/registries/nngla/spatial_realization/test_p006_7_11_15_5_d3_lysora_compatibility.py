import re
from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_polygonization import build_atomic_face_set, source_fabric_diagnostics
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope


def _snapshot():
    scope = resolve_initial_fabric_scope("NG-PLC-000518")
    defects = source_fabric_diagnostics(scope)
    graph = build_shared_edge_graph(scope)
    faces = build_atomic_face_set(scope, graph)
    return scope, defects, graph, faces


def test_d3_1_lysora_geometrycollection_residual_is_diagnostic_not_traceback():
    scope, defects, graph, faces = _snapshot()
    assert scope.parent.subject_id == "NG-ADM-000147"
    assert len(defects) == 5
    assert any(item.residual_class == "MICRO_BOUNDARY_RESIDUAL" for item in defects)
    assert len(graph.edges) == 136
    assert len(faces.faces) == 11
    assert len(faces.governed_face_ids) == 2
    assert re.fullmatch(r"[0-9a-f]{64}", faces.face_set_sha256)


def test_d3_1_lysora_replay_is_deterministic_within_runtime():
    first = _snapshot(); second = _snapshot()
    assert first[2].graph_sha256 == second[2].graph_sha256
    assert first[3].face_set_sha256 == second[3].face_set_sha256
    assert [(d.kind.value,d.geometry_sha256,d.residual_class,d.adjacent_subject_ids) for d in first[1]] == [
        (d.kind.value,d.geometry_sha256,d.residual_class,d.adjacent_subject_ids) for d in second[1]
    ]
