from registries.nngla.spatial_fabric.qualification import bundle17a_is_qualified, qualify_sources, qualify_topology


def test_source_and_topology_qualification_are_fully_green_without_postgresql():
    source = qualify_sources()
    topology = qualify_topology()
    assert len(source) == 47
    assert len(topology) == 1120
    assert all(row.contract_status == "PASS" for row in source)
    assert all(row.topology_status == "PASS" for row in topology)
    assert sum(row.finding_count for row in topology) == 0
    assert bundle17a_is_qualified()
