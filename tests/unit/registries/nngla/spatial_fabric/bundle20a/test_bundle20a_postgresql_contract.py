from registries.nngla.spatial_fabric.bundle20a.postgresql_contract import schema_findings

def test_bundle20a_schema_is_additive_and_complete(): assert schema_findings()==()
