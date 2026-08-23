import csv,json
from registries.nngla.spatial_fabric.bundle20a.materialize import materialize
from registries.nngla.spatial_fabric.bundle20a._shared import ROAD_GEOMETRIES,ROAD_SEGMENTS,NETWORK_NODES,SUMMARY

def test_materialized_artifacts_are_complete():
    c=materialize(); assert c['roads']==350 and c['segments']==350 and c['connections']==700 and c['junction_nodes']>0
    assert len(json.load(open(ROAD_GEOMETRIES))['features'])==350
    assert len(list(csv.DictReader(open(ROAD_SEGMENTS))))==350
    assert len(list(csv.DictReader(open(NETWORK_NODES))))==c['nodes']
    assert json.load(open(SUMMARY))['publication_status']=='NOT_PUBLISHED'
