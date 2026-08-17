from registries.nngla.spatial_fabric.bundle17d import bundle17d_is_qualified, marine_qualification_findings, marine_source_findings


def test_bundle17d_is_fully_qualified_without_canonical_persistence_or_naming():
    assert marine_source_findings() == ()
    assert marine_qualification_findings() == ()
    assert bundle17d_is_qualified()
