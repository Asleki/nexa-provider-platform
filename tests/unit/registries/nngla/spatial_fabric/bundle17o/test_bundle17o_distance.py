from registries.nngla.spatial_fabric.bundle17o.contracts import SpatialReadRecord
from registries.nngla.spatial_fabric.bundle17o.distance_queries import distance_between,nearest
def rec(i,lon,lat):
    return SpatialReadRecord(i,"GEOGRAPHIC_FEATURE",i,"production","PUBLIC",f"NG-GEO-{i[-1]:0>6}",1,1,lon,lat)
def test_distance_is_explicit_metric_measurement_and_nearest_is_ordering():
    a=rec("a1",31.0,-18.0); b=rec("b2",31.01,-18.0); c=rec("c3",32.0,-18.0)
    m=distance_between(a,b)
    assert m.distance_unit=="m" and m.measurement_basis=="WGS84_GEODESIC_REFERENCE" and m.distance_value>0
    assert nearest(a,(c,b),limit=1)[0].to_subject_id=="b2"
