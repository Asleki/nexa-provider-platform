from registries.nngla.spatial_fabric.bundle17o import *
def test_query_service_find_geocode_distance_and_frontage():
    road=SpatialReadRecord("NG-RD-000001","ROAD","Road","production","PUBLIC","NG-GEO-000001",1,1,31.0,-18.0)
    river=SpatialReadRecord("NG-FEAT-000001","GEOGRAPHIC_FEATURE","River","production","PUBLIC","NG-GEO-000002",1,1,31.1,-18.0)
    repo=MemorySpatialReadRepository((road,river))
    topo=MemoryTopologyBackend((RelationshipEvidence("site:1","FRONTS",road.subject_id,"frontage:nngla:1",road.geometry_id,1),))
    geo=MemoryGeocoder((GeocodeMatch(road.subject_id,"NG-NAM-000001","ROAD","Road","scope:1","PUBLIC",road.geometry_id,1),))
    svc=SpatialQueryService(repo,topology_backend=topo,geocoder=geo)
    q=SpatialQueryRequest("FIND_BY_CANONICAL_ID",1,"production",{"subject_id":road.subject_id})
    assert svc.execute(q).records[0].subject_id==road.subject_id
    q=SpatialQueryRequest("SPATIAL_DISTANCE",1,"production",{"subject_id":road.subject_id,"object_id":river.subject_id})
    assert svc.execute(q).records[0].distance_unit=="m"
    q=SpatialQueryRequest("SPATIAL_FRONTS",1,"production",{"subject_id":"site:1"})
    assert svc.execute(q).records[0].object_id==road.subject_id
    q=SpatialQueryRequest("GEOCODE",1,"production",{"text":"road"})
    assert svc.execute(q).records[0].status.value=="UNIQUE_MATCH"
