from collections import Counter
from registries.nngla.spatial_fabric.bundle20a.authoring import author_road_alignments

def test_authors_exact_locked_350_roads_and_seven_classes():
    roads=author_road_alignments()
    assert len(roads)==350 and len({r.road_id for r in roads})==350
    assert Counter(r.road_class_code for r in roads)==Counter({k:50 for k in ('ACCESS','DISTRICT','LOCAL','MUNICIPAL','REGIONAL','RURAL','SERVICE')})
    assert all(r.qualification_status=='QUALIFIED_SIMULATION_AUTHORED' and r.provenance_class=='NNGLA_SIMULATION_AUTHORED_ALIGNMENT' for r in roads)

def test_road_geometry_is_metric_and_endpoint_bound():
    roads=author_road_alignments()
    assert min(r.length_m for r in roads)>0
    assert all(r.start_place_id!=r.end_place_id for r in roads)
    assert all(r.geometry_reservation_key==f'p006.7.11.12:road-alignment:{r.road_id}' for r in roads)
