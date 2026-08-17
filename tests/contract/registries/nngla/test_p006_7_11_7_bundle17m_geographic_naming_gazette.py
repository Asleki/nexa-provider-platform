
from registries.nngla.spatial_fabric.bundle17m import *

def test_bundle17m_contract_is_data_driven_across_all_current_name_families(): assert bundle17m_is_qualified() and len(name_families())==19 and governed_name_count()==6240

def test_bundle17m_contract_keeps_feature_identity_independent_from_rename_history():
    results=assignment_results(); assert all(r.subject_id.startswith(('river:','lake:','landform:')) for r in results); assert all(r.assignment_role=='PRIMARY' for r in results)

def test_bundle17m_contract_does_not_promote_proposed_assignments_or_fabricate_gazette_effect(): assert all(r.source_assignment_status=='PROPOSED_UNGAZETTED' and not r.official_effect for r in assignment_results()) and gazette_candidates()==()
