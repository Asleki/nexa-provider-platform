from registries.nngla.spatial_fabric.bundle17h import bundle17h_findings, bundle17h_is_qualified


def test_bundle17h_is_fully_qualified():
    assert bundle17h_findings() == ()
    assert bundle17h_is_qualified() is True
