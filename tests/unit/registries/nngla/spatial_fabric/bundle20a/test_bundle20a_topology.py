from registries.nngla.spatial_fabric.bundle20a.topology import build_network

def test_network_has_one_segment_per_canonical_road_and_endpoint_connections():
    nodes,segs,conns=build_network()
    assert len(segs)==350 and len(conns)==700
    assert len({s.road_id for s in segs})==350
    assert any(n.node_role=='JUNCTION' for n in nodes)
    assert all(s.start_node_id!=s.end_node_id for s in segs)
