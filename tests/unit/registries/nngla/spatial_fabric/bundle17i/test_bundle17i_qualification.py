from registries.nngla.spatial_fabric.bundle17i import bundle17i_findings, bundle17i_is_qualified


def test_bundle17i_is_qualified():
    assert bundle17i_findings() == ()
    assert bundle17i_is_qualified()
