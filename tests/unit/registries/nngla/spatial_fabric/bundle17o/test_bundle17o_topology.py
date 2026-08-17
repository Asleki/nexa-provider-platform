import pytest
from registries.nngla.spatial_fabric.bundle17o.contracts import QueryOperator
from registries.nngla.spatial_fabric.bundle17o.topology_queries import PERSISTED_RELATIONSHIP_MAPPING,RelationshipEvidence,MemoryTopologyBackend
def test_query_operator_is_distinct_from_persisted_relationship_vocabulary():
    assert PERSISTED_RELATIONSHIP_MAPPING[QueryOperator.ADJACENT]=="ADJACENT_TO"
    assert QueryOperator.NEAREST not in PERSISTED_RELATIONSHIP_MAPPING
    b=MemoryTopologyBackend((RelationshipEvidence("site:1","FRONTS","NG-RD-000001","frontage:nngla:1"),))
    assert b.query(QueryOperator.FRONTS,"site:1")[0].object_id=="NG-RD-000001"
    with pytest.raises(ValueError): b.query(QueryOperator.NEAREST,"site:1")
