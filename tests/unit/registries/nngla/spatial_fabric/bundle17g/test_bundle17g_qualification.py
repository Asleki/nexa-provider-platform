from registries.nngla.spatial_fabric.bundle17g import bundle17g_findings, bundle17g_is_qualified


def test_bundle17g_qualifies_operational_contract_without_fake_registered_land():
    assert bundle17g_findings() == ()
    assert bundle17g_is_qualified()
