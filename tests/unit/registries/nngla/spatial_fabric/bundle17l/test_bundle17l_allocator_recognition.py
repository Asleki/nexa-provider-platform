
import pytest
from registries.nngla.spatial_fabric.bundle17l import *

def test_allocator_starts_after_locked_21_and_is_idempotent():
    a=MemoryFeatureIdAllocator(); x=a.reserve(candidate_id='featcand:nngla:x',idempotency_key='x'); assert x=='NG-FEAT-000022' and a.reserve(candidate_id='featcand:nngla:x',idempotency_key='x')==x

def test_simulation_cannot_consume_sovereign_feature_identity():
    with pytest.raises(ValueError): MemoryFeatureIdAllocator().reserve(candidate_id='featcand:nngla:x',idempotency_key='x',authority_runtime_mode='simulation')

def test_existing_canonical_reuse_never_allocates_replacement_identity():
    c=next(x for x in recognition_candidates() if x.existing_canonical_feature_id=='NG-FEAT-000010'); r=recognize_candidate(c,idempotency_key='existing'); assert r.disposition.value=='REUSE_CANONICAL' and r.canonical_feature_id=='NG-FEAT-000010'

def test_qualified_island_needs_production_and_gets_new_identity_only_at_recognition():
    c=next(x for x in recognition_candidates() if x.feature_type_code=='ISLAND' and not x.existing_canonical_feature_id); q=qualify_candidate(c); assert q.disposition.value=='RECOGNIZE_NEW' and q.canonical_feature_id==''; r=recognize_candidate(c,allocator=MemoryFeatureIdAllocator(),idempotency_key='island'); assert r.canonical_feature_id=='NG-FEAT-000022'
