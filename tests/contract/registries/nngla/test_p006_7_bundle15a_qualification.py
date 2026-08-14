from registries.nngla.bundle15a_qualification import qualify_bundle15a, QUALIFICATION_ID

def test_bundle15a_qualification_is_green_and_source_counts_are_preserved():
    receipt=qualify_bundle15a()
    assert receipt.qualification_id==QUALIFICATION_ID
    assert receipt.status=='QUALIFIED'
    assert receipt.findings==()
    assert receipt.recognized_feature_candidate_count==21
    assert receipt.settlement_place_count==700
    assert receipt.administrative_candidate_count==192
    assert receipt.feature_name_assignment_count==20

def test_bundle15a_qualification_does_not_claim_geometry_or_gazette_completion():
    receipt=qualify_bundle15a()
    assert receipt.status=='QUALIFIED'
    assert not any('geometry' in x and 'qualified' in x for x in receipt.findings)
