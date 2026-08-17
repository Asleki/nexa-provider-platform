from registries.nngla.spatial_fabric.bundle17d import effective_feature_type_codes, feature_type_extension_rows


def test_bundle17d_adds_only_missing_marine_coastal_feature_types():
    rows = feature_type_extension_rows()
    assert len(rows) == 5
    assert {row["feature_type_code"] for row in rows} == {"OCEAN", "ESTUARY", "NATURAL_HARBOUR", "BEACH", "CLIFF"}
    assert all(row["nngla_recognizable"] == "true" for row in rows)
    assert all(row["nngla_creatable"] == "false" for row in rows)
    effective = effective_feature_type_codes()
    assert {"BAY", "CAPE", "COASTLINE", "ISLAND", "OCEAN", "ESTUARY", "NATURAL_HARBOUR", "BEACH", "CLIFF"} <= effective
