from registries.nngla.spatial_fabric.bundle19a.qualification import bundle19a_is_qualified, qualification_findings


def test_bundle19a_full_static_spatial_qualification_is_green():
    assert qualification_findings() == ()
    assert bundle19a_is_qualified() is True
