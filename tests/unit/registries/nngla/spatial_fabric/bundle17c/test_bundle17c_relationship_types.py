from registries.nngla.spatial_fabric.bundle17c import relationship_type_rows


def test_bundle17c_relationship_vocabulary_contains_locked_core_relations():
    rows = relationship_type_rows()
    assert len(rows) == 10
    codes = {row["relationship_type_code"] for row in rows}
    assert codes == {
        "CONTAINS", "WITHIN", "INTERSECTS", "CROSSES", "TOUCHES",
        "OVERLAPS", "ADJACENT_TO", "NEAR", "FRONTS", "CONNECTED_TO",
    }
    assert all(row["compatibility_semantics"] == "RELATIONSHIP_FACT_IS_SEPARATE_FROM_POLICY_OUTCOME" for row in rows)
