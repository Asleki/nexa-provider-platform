from collections import Counter

from registries.nngla.spatial_fabric.bundle17c import bundle17c_is_qualified, derive_conflict_qualification_results


def test_bundle17c_qualifies_current_reference_relations_without_faking_full_extent():
    rows = derive_conflict_qualification_results()
    assert len(rows) == 34
    assert Counter(row.qualification_status for row in rows) == Counter({"PASS_WITH_DEFERRED_GEOMETRY": 34})
    assert all(row.conflict_status.value == "NOT_EVALUABLE_PENDING_GEOMETRY" for row in rows)
    assert all("FULL_EXTENT_CONFLICT_CHECK_DEFERRED" in row.findings for row in rows)
    assert bundle17c_is_qualified()
