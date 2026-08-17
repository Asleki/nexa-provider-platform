import pytest
from registries.nngla.spatial_fabric.bundle17o.contracts import SpatialQueryRequest,QueryOperator,BoundaryPolicy
def test_query_contract_normalizes_runtime_and_limits():
    q=SpatialQueryRequest("SPATIAL_CONTAINS",1,"PRODUCTION",{"subject_id":"a"},BoundaryPolicy.INCLUDE_BOUNDARY,100)
    assert q.runtime_mode.value=="production" and QueryOperator.NEAREST.value=="NEAREST"
    with pytest.raises(ValueError): SpatialQueryRequest("X",1,"production",{},limit=1001)
