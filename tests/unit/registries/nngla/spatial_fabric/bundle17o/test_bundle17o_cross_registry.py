from registries.nngla.spatial_fabric.bundle17o.cross_registry import reference_allowed,reference_contracts
def test_cross_registry_contracts_reference_without_embedding():
    assert reference_allowed("HEALTH","ADDRESSABLE_SITE","FACILITY_SITE")
    assert reference_allowed("NEXAPOS","ADDRESSABLE_SITE","OUTLET_SITE")
    assert all(r["embedding_policy"]=="REFERENCE_ONLY" for r in reference_contracts())
