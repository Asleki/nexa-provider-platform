from registries.nngla.spatial_fabric.bundle17c.occupancy import candidate_source_rows


def test_bundle17c_preserves_governed_empty_hill_forest_and_wetland_sources_without_fabrication():
    rows = candidate_source_rows()
    types = {row["feature_type"] for _, row in rows}
    assert "HILL" not in types
    assert "FOREST" not in types
    assert "WETLAND" not in types
    assert len(rows) == 23
