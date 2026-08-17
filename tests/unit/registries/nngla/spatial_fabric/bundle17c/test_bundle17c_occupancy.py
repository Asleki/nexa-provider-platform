from collections import Counter

from registries.nngla.spatial_fabric.bundle17c import derive_occupancy_relationships


def test_bundle17c_derives_real_qualified_occupancy_without_empty_used_semantics():
    rows = derive_occupancy_relationships()
    assert len(rows) == 34
    assert len({row.relationship_evidence_id for row in rows}) == 34
    assert Counter(row.relationship_type_code.value for row in rows) == Counter({"TOUCHES": 22, "WITHIN": 12})
    assert all(row.qualification_status == "PASS" for row in rows)
    assert all("EMPTY" not in row.relationship_basis and "USED" not in row.relationship_basis for row in rows)


def test_bundle17c_point_and_coastal_relationships_preserve_evidence_limits():
    rows = derive_occupancy_relationships()
    point_rows = [row for row in rows if row.relationship_type_code.value == "WITHIN"]
    coastal_rows = [row for row in rows if row.relationship_type_code.value == "TOUCHES"]
    assert len(point_rows) == 12
    assert len(coastal_rows) == 22
    assert all("does not assert the full physical feature extent" in row.notes for row in point_rows)
    assert all("not yet a completed physical feature geometry" in row.notes for row in coastal_rows)
