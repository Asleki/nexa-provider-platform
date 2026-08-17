from registries.nngla.spatial_fabric.bundle17f import bundle17f_findings, bundle17f_is_qualified


def test_bundle17f_is_green_without_inventing_geometry_or_canonical_road_rows():
    assert bundle17f_findings() == ()
    assert bundle17f_is_qualified() is True
