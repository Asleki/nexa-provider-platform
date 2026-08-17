
from registries.nngla.spatial_fabric.bundle17l import *

def test_bundle17l_contract_adds_supported_feature_instances_without_type_specific_python():
    assert bundle17l_is_qualified(); assert len(qualification_rules())==22; assert len(recognition_candidates())==37

def test_bundle17l_contract_preserves_existing_21_and_defers_unready_coastal_evidence():
    c=recognition_candidates(); assert {x.existing_canonical_feature_id for x in c if x.existing_canonical_feature_id}=={f'NG-FEAT-{i:06d}' for i in range(1,22)}; assert all(qualify_candidate(x).disposition.value=='DEFER' for x in c if x.candidate_status=='DEFERRED_PENDING_PHYSICAL_GEOMETRY')

def test_bundle17l_contract_keeps_simulation_candidate_formation_separate_from_production_recognition():
    c=next(x for x in recognition_candidates() if x.feature_type_code=='ISLAND' and not x.existing_canonical_feature_id)
    try: recognize_candidate(c,idempotency_key='sim',authority_runtime_mode='simulation',has_observation=True,spatial_valid=True,environment_resolved=True,conflict_free=True)
    except ValueError: pass
    else: raise AssertionError('simulation consumed sovereign feature identity')
