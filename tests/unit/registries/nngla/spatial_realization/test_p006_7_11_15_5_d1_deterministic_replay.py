from shapely import from_wkb

from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.face_assignment import assign_atomic_faces
from registries.nngla.spatial_realization.face_polygonization import build_atomic_face_set
from registries.nngla.spatial_realization.fabric_qualification import qualify_candidate_fabric
from registries.nngla.spatial_realization.fabric_scope import build_recursive_child_scope, resolve_initial_fabric_scope

from _delivery1_test_support import governance_fixture_decisions


def _run(scope, overrides=None, reverse_decisions=False):
    graph = build_shared_edge_graph(scope, geometry_overrides=overrides)
    faces = build_atomic_face_set(scope, graph, geometry_overrides=overrides)
    face_decisions, boundary_decisions = governance_fixture_decisions(scope, faces)
    if reverse_decisions:
        face_decisions = tuple(reversed(face_decisions))
        boundary_decisions = tuple(reversed(boundary_decisions))
    assignment = assign_atomic_faces(
        scope,
        faces,
        face_decisions=face_decisions,
        boundary_conflict_decisions=boundary_decisions,
        geometry_overrides=overrides,
    )
    qualification = qualify_candidate_fabric(scope, faces, assignment, geometry_overrides=overrides)
    return graph, faces, assignment, qualification


def test_delivery1_northgate_replay_is_stable_even_when_decision_input_order_is_reversed():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    first = _run(scope)
    second = _run(scope, reverse_decisions=True)
    assert first[0].graph_sha256 == second[0].graph_sha256
    assert first[1].face_set_sha256 == second[1].face_set_sha256
    assert first[2].assignment_sha256 == second[2].assignment_sha256
    assert first[3].qualification_sha256 == second[3].qualification_sha256
    assert [(c.subject_id, c.geometry_sha256) for c in first[2].sibling_candidates] == [
        (c.subject_id, c.geometry_sha256) for c in second[2].sibling_candidates
    ]


def test_delivery1_nyara_to_silvermere_recursive_replay_preserves_parent_candidate_hash_chain():
    region_scope = resolve_initial_fabric_scope(
        "NG-PLC-000258", material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED",)
    )
    first_region = _run(region_scope)
    second_region = _run(region_scope, reverse_decisions=True)
    assert first_region[3].prototype_ready and second_region[3].prototype_ready
    a = first_region[2].candidate_by_subject["NG-ADM-000078"]
    b = second_region[2].candidate_by_subject["NG-ADM-000078"]
    assert (a.candidate_id, a.geometry_sha256) == (b.candidate_id, b.geometry_sha256)

    child_scope_a = build_recursive_child_scope(
        region_scope, "NG-ADM-000078",
        qualified_parent_geometry_sha256=a.geometry_sha256,
        qualified_parent_candidate_id=a.candidate_id,
    )
    child_scope_b = build_recursive_child_scope(
        region_scope, "NG-ADM-000078",
        qualified_parent_geometry_sha256=b.geometry_sha256,
        qualified_parent_candidate_id=b.candidate_id,
    )
    assert child_scope_a.fingerprint == child_scope_b.fingerprint
    override_a = {"NG-ADM-000078": from_wkb(bytes.fromhex(a.geometry_wkb_hex))}
    override_b = {"NG-ADM-000078": from_wkb(bytes.fromhex(b.geometry_wkb_hex))}
    first_child = _run(child_scope_a, override_a)
    second_child = _run(child_scope_b, override_b, reverse_decisions=True)
    assert first_child[0].graph_sha256 == second_child[0].graph_sha256
    assert first_child[1].face_set_sha256 == second_child[1].face_set_sha256
    assert first_child[2].assignment_sha256 == second_child[2].assignment_sha256
    assert first_child[3].qualification_sha256 == second_child[3].qualification_sha256
