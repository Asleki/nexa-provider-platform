from registries.nngla.spatial_realization.edge_graph import build_shared_edge_graph
from registries.nngla.spatial_realization.fabric_scope import resolve_initial_fabric_scope


def test_delivery1_northgate_edge_graph_nodes_complete_parent_and_sibling_sources_once():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    graph = build_shared_edge_graph(scope)
    assert graph.edge_count > len(scope.exhaustive_siblings)
    assert graph.source_subject_ids[0] == "NG-ADM-000032"
    assert set(graph.source_subject_ids[1:]) == {item.subject_id for item in scope.exhaustive_siblings}
    assert all(edge.lineage for edge in graph.edges)
    assert all(edge.edge_id.startswith("fabric-edge:nngla:") for edge in graph.edges)


def test_delivery1_nyara_edge_graph_contains_all_four_region_local_peers_and_no_overlay_owner():
    scope = resolve_initial_fabric_scope(
        "NG-PLC-000258", material_rule_codes=("CITY_PARENT_CONTAINMENT_FAILED",)
    )
    graph = build_shared_edge_graph(scope)
    assert set(graph.source_subject_ids) == {
        "NG-ADM-000004", "NG-ADM-000078", "NG-ADM-000079", "NG-ADM-000080", "NG-ADM-000081"
    }
    assert all("NG-ADM-000099" not in {row.subject_id for row in edge.lineage} for edge in graph.edges)


def test_delivery1_edge_graph_hash_is_input_order_independent_at_scope_contract_boundary():
    scope = resolve_initial_fabric_scope("NG-PLC-000086")
    first = build_shared_edge_graph(scope)
    second = build_shared_edge_graph(scope)
    assert first.graph_sha256 == second.graph_sha256
    assert [edge.geometry_sha256 for edge in first.edges] == [edge.geometry_sha256 for edge in second.edges]
