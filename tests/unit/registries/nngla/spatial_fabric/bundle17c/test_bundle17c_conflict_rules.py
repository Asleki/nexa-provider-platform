from registries.nngla.spatial_fabric.bundle17c import conflict_rule_set_rows


def test_bundle17c_rule_sets_reserve_additive_extension_points():
    rows = conflict_rule_set_rows()
    assert len(rows) == 5
    assert {row["rule_scope"] for row in rows} == {"NATURAL_FEATURE", "COASTAL", "TRANSPORT", "SETTLEMENT", "CADASTRE"}
    assert all(row["extension_policy"] == "ADD_RULE_ROWS_NOT_ENGINE_BRANCHES" for row in rows)
    assert next(row for row in rows if row["rule_scope"] == "CADASTRE")["unresolved_geometry_outcome"] == "BLOCK"
