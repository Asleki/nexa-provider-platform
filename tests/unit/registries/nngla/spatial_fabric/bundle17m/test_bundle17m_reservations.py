
import pytest
from registries.nngla.spatial_fabric.bundle17m import *

def test_family_allocator_extends_occupied_namespace_without_hardcoded_global_counter():
    a=MemoryNameIdAllocator(); assert a.reserve(family_code='RIVER',idempotency_key='r')=='NG-NAM-RIV-000321'; assert a.reserve(family_code='SEA_ROUTE',idempotency_key='s')=='NG-NAM-SEA-000181'

def test_name_reservation_is_idempotent_and_scope_aware():
    r=MemoryNameReservationRepository(); a=r.reserve(reservation_id='nameres:nngla:a',family_code='RIVER',display_name='Crown River',scope_type='REGION',scope_reference='A',idempotency_key='a'); assert r.reserve(reservation_id='nameres:nngla:ignored',family_code='RIVER',display_name='Crown River',scope_type='REGION',scope_reference='A',idempotency_key='a')==a; b=r.reserve(reservation_id='nameres:nngla:b',family_code='RIVER',display_name='Crown River',scope_type='REGION',scope_reference='B',idempotency_key='b'); assert a.reserved_name_id!=b.reserved_name_id

def test_same_family_same_scope_same_normalized_name_collides():
    r=MemoryNameReservationRepository(); r.reserve(reservation_id='nameres:nngla:a',family_code='RIVER',display_name=' Crown   River ',scope_type='REGION',scope_reference='A',idempotency_key='a')
    with pytest.raises(ValueError): r.reserve(reservation_id='nameres:nngla:b',family_code='RIVER',display_name='crown river',scope_type='REGION',scope_reference='A',idempotency_key='b')

def test_simulation_cannot_reserve_sovereign_name_id():
    with pytest.raises(ValueError): MemoryNameIdAllocator().reserve(family_code='RIVER',idempotency_key='sim',authority_runtime_mode='simulation')
