from registries.nngla.spatial_fabric.bundle17h import derive_road_segment_candidates, form_frontage_candidate, form_site_candidate


def test_bundle17h_derives_one_subordinate_non_destructive_segment_candidate_for_each_locked_road():
    rows = derive_road_segment_candidates()
    assert len(rows) == 350
    assert rows[0].road_id == "NG-RD-000001"
    assert rows[-1].road_id == "NG-RD-000350"
    assert all(row.source_road_candidate_id == f"NG-RD-CAND-{i:06d}" for i,row in enumerate(rows, start=1))
    assert all(row.segment_role == "PROVISIONAL_WHOLE_ROAD_ADDRESS_SCOPE" for row in rows)
    assert all(row.geometry_status == "DEFERRED_NO_ROAD_GEOMETRY" for row in rows)


def test_frontage_is_typed_relationship_not_nearest_road_guess():
    segment = derive_road_segment_candidates()[0]
    site = form_site_candidate(road_id=segment.road_id, road_segment_id=segment.road_segment_id, source_reference="test:site")
    frontage = form_frontage_candidate(site, segment, source_reference="test:frontage")
    assert frontage.site_id == site.site_id
    assert frontage.road_id == "NG-RD-000001"
    assert frontage.qualification_status == "PENDING_GEOMETRY_OR_SURVEY"
