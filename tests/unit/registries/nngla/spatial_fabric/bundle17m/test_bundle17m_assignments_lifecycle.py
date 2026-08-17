
from registries.nngla.spatial_fabric.bundle17m import *

def test_existing_20_proposals_are_preserved_ungazetted_and_not_official():
    a=existing_assignment_candidates(); r=assignment_results(); assert len(a)==20 and len(r)==20 and all(x.result_status=='PRESERVED_PROPOSED_UNGAZETTED' and not x.official_effect and not x.gazette_reference for x in r)

def test_assignment_roles_remain_a_separate_dimension_even_where_historic_code_is_shared():
    statuses=naming_status_codes(); assert {'PRIMARY','ALTERNATE','NICKNAME'}.isdisjoint(statuses); assert 'HISTORIC' in statuses and 'HISTORICAL' not in statuses; assert all('HISTORIC' in r.allowed_assignment_roles for r in assignment_rules())

def test_approved_is_not_gazetted_and_legal_effect_is_gated():
    assert transition_allowed('UNDER_REVIEW','APPROVED',approved=True); assert not transition_allowed('GAZETTE_PENDING','GAZETTED',approved=True,gazetted=False); assert transition_allowed('GAZETTE_PENDING','GAZETTED',approved=True,gazetted=True)
