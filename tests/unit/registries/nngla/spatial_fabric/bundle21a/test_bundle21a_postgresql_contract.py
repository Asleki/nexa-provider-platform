from registries.nngla.spatial_fabric.bundle21a.postgresql_contract import schema_findings

def test_publication_schema_adds_ledger_without_replacing_projection(): assert schema_findings()==()
