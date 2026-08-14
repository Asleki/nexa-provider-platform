from registries.nngla.bundle15b_qualification import QUALIFICATION_ID,qualify_bundle15b

def test_bundle15b_qualifies_real_source_counts_without_fabricating_empty_registers():
    r=qualify_bundle15b(); assert r.qualification_id==QUALIFICATION_ID; assert r.status=='QUALIFIED'; assert r.findings==()
    assert (r.geometry_candidate_count,r.survey_control_candidate_count,r.road_candidate_count,r.address_candidate_count)==(21,0,900,0)

def test_bundle15b_uses_full_controlled_vocabularies():
    r=qualify_bundle15b(); assert r.survey_accuracy_class_count==6; assert r.road_class_count==10; assert r.geometry_type_count==6; assert r.crs_count==1
