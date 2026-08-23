from registries.nngla.spatial_fabric.bundle20a.authoring import author_road_alignments
from registries.nngla.spatial_fabric.bundle20a.topology import build_network
from registries.nngla.spatial_fabric.bundle20a.relationships import derive_relationships

def test_p006_7_11_12_locked_contract():
    roads=author_road_alignments(); nodes,segs,conns=build_network(roads); rels=derive_relationships(roads)
    assert len(roads)==350 and len(segs)==350 and len(conns)==700
    assert all(r.road_id.startswith('NG-RD-') and r.geometry_reservation_key.startswith('p006.7.11.12:') for r in roads)
    assert all(r.provenance_class=='NNGLA_SIMULATION_AUTHORED_ALIGNMENT' for r in roads)
    assert all(r.evidence_basis=='GEOMETRIC_INTERSECTION_NOT_BRIDGE_ASSERTION' for r in rels if r.relationship_type=='CROSSES_RIVER')
