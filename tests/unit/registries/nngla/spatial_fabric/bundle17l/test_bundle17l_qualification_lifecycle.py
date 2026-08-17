
from registries.nngla.spatial_fabric.bundle17l import *

def test_pending_coastal_reserve_fails_closed_until_physical_geometry_exists():
    c=next(x for x in recognition_candidates() if x.feature_type_code=='BAY' and not x.existing_canonical_feature_id); r=qualify_candidate(c); assert r.disposition.value=='DEFER' and not r.qualified and not r.geometry_ready

def test_lifecycle_transition_is_data_driven_and_production_gated():
    assert transition_allowed('DETECTED','DISCOVERED',runtime_mode='simulation'); assert not transition_allowed('CLASSIFIED','RECOGNIZED',runtime_mode='simulation'); assert transition_allowed('CLASSIFIED','RECOGNIZED',runtime_mode='production'); assert transition_allowed('ACTIVE','EXTINCT',runtime_mode='production')
