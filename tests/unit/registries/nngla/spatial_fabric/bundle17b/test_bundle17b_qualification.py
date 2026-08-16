from registries.nngla.spatial_fabric.bundle17b.qualification import bundle17b_is_qualified, qualify_bundle17b


def test_bundle17b_qualification_is_fail_closed_and_green_only_when_every_layer_is_clean():
    result = qualify_bundle17b()
    assert result.qualification_status == "PASS"
    assert result.crs_crosswalk_finding_count == 0
    assert result.precision_record_count == 10644
    assert result.precision_finding_count == 0
    assert result.containment_record_count == 2411
    assert result.containment_finding_count == 0
    assert result.source_fidelity_record_count == 5322
    assert result.source_fidelity_finding_count == 0
    assert result.environment_binding_count == 1104
    assert result.environment_finding_count == 0
    assert result.environment_coverage_count == 1104
    assert bundle17b_is_qualified()
