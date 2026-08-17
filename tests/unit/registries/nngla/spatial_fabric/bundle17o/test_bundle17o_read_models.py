from registries.nngla.spatial_fabric.bundle17o import SpatialReadRecord,SpatialQueryPrincipal,SpatialQueryRequest,SpatialQueryService
from registries.nngla.spatial_fabric.bundle17o.read_models import MemorySpatialReadRepository
def test_read_repository_and_service_enforce_runtime_and_visibility_without_identity_rewrite():
    pub=SpatialReadRecord("NG-PLC-000001","PLACE","A","production","PUBLIC","NG-GEO-000001",1,1)
    restricted=SpatialReadRecord("NG-TTL-000001","TITLE","T","production","RESTRICTED",None,None,1)
    repo=MemorySpatialReadRepository((pub,restricted)); svc=SpatialQueryService(repo)
    q=SpatialQueryRequest("FIND_BY_CANONICAL_ID",1,"production",{"subject_id":restricted.subject_id})
    assert svc.execute(q).records==()
    principal=SpatialQueryPrincipal("authorized:1","production",frozenset({"nngla.read.restricted"}))
    assert svc.execute(q,principal).records[0].subject_id==restricted.subject_id
    wrong=SpatialQueryPrincipal("wrong:1","simulation",principal.permissions)
    import pytest
    with pytest.raises(PermissionError): svc.execute(q,wrong)
