from registries.nngla.spatial_fabric.bundle17o.contracts import SpatialReadRecord,BoundaryPolicy
from registries.nngla.spatial_fabric.bundle17o.reverse_geocoding import PolygonReadRecord,MemoryReverseGeocoder
def test_reverse_geocode_returns_typed_containment_stack_and_boundary_policy():
    admin=SpatialReadRecord("NG-ADM-001","ADMINISTRATIVE_AREA","Region","production","PUBLIC","NG-GEO-000001",1,1)
    parcel=SpatialReadRecord("NV-01-001-0001","PARCEL","Parcel","production","PUBLIC","NG-GEO-000002",1,1)
    ring=((0,0),(10,0),(10,10),(0,10),(0,0))
    g=MemoryReverseGeocoder((PolygonReadRecord(admin,ring,1),PolygonReadRecord(parcel,ring,2)))
    assert [r.family for r in g.reverse(5,5,runtime_mode="production")]==["ADMINISTRATIVE_AREA","PARCEL"]
    assert g.reverse(0,5,runtime_mode="production",boundary_policy=BoundaryPolicy.STRICT_INTERIOR)==()
    assert len(g.reverse(0,5,runtime_mode="production",boundary_policy=BoundaryPolicy.INCLUDE_BOUNDARY))==2
