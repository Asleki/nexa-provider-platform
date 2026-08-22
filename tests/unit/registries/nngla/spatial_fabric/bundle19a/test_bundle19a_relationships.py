from registries.nngla.spatial_fabric.bundle19a.relationships import derive_place_spatial_relationships


def test_all_668_source_parent_links_receive_spatial_evidence_without_legalization():
    rows = derive_place_spatial_relationships()
    assert len(rows) == 668
    assert len({r.child_place_id for r in rows}) == 668
    assert all(r.qualification_status == "PASS" for r in rows)
    assert all("NOT_LEGAL_CONTAINMENT" in r.relationship_basis for r in rows)


def test_parent_relation_does_not_falsely_claim_near_for_all_places():
    rows = derive_place_spatial_relationships()
    assert {r.parent_footprint_relation for r in rows} <= {"WITHIN", "OUTSIDE", "PARENT_HAS_NO_FOOTPRINT"}
    assert all(r.distance_m >= 0 for r in rows)
