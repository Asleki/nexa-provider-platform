from registries.nngla.spatial_fabric.bundle17o import *
def test_p006_7_11_7_19_cross_registry_queries_need_no_internal_table_knowledge():
    assert bundle17o_is_qualified()
    place=SpatialReadRecord("NG-PLC-000001","PLACE","Capital","simulation","PUBLIC","NG-GEO-000001",3,2,31.0,-18.0)
    river=SpatialReadRecord("NG-FEAT-000021","GEOGRAPHIC_FEATURE","River","simulation","PUBLIC","NG-GEO-000021",2,2,31.02,-18.0)
    repo=MemorySpatialReadRepository((place,river))
    geocoder=MemoryGeocoder((GeocodeMatch(place.subject_id,"NG-NAM-000001","PLACE","Capital","country:novegeo","PUBLIC",place.geometry_id,place.geometry_version,"simulation"),))
    service=SpatialQueryService(repo,geocoder=geocoder,read_model_version=2)
    found=service.execute(SpatialQueryRequest("FIND_BY_CANONICAL_ID",1,"simulation",{"subject_id":place.subject_id}))
    assert found.records[0].subject_id=="NG-PLC-000001" and found.read_model_version==2
    nearest_result=service.execute(SpatialQueryRequest("SPATIAL_NEAREST",1,"simulation",{"subject_id":place.subject_id,"family":"GEOGRAPHIC_FEATURE"}))
    assert nearest_result.records[0].to_subject_id=="NG-FEAT-000021"
    geo=service.execute(SpatialQueryRequest("GEOCODE",1,"simulation",{"text":" capital "}))
    assert geo.records[0].matches[0].subject_id==place.subject_id
