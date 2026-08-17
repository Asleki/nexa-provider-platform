
from registries.nngla.spatial_fabric.bundle17m import *

def test_no_gazette_actions_are_fabricated_from_existing_proposals(): assert len(gazette_candidates())==0

def test_simulation_can_form_candidate_but_not_claim_legal_effect():
    c=form_gazette_candidate(subject_id='NG-FEAT-000002',name_id='NG-NAM-RIV-000001',gazette_action_code='NAME',proposed_effective_on='2026-08-18'); assert c.runtime_mode=='simulation' and c.candidate_status=='CANDIDATE'
