from __future__ import annotations
from registries.nngla.spatial_fabric.bundle17h import AddressNumberCollisionError,AddressSeriesDefinition,MemoryAddressAllocator,form_site_candidate
from .contracts import RecoveryResult

def idempotent_address_replay():
    series=AddressSeriesDefinition('addrseries:nngla:17j-replay','NG-RD-000001','','SEQUENTIAL','ROAD','NG-RD-000001',1,1,'INTEGER','NONE',False)
    a=MemoryAddressAllocator(); site=form_site_candidate(road_id='NG-RD-000001',source_reference='17j:replay')
    x=a.reserve_next(series,site_id=site.site_id,idempotency_key='same-request'); y=a.reserve_next(series,site_id=site.site_id,idempotency_key='same-request')
    return x==y

def collision_contract():
    series=AddressSeriesDefinition('addrseries:nngla:17j-collision','NG-RD-000001','','SEQUENTIAL','ROAD','NG-RD-000001',1,1,'INTEGER','NONE',False)
    a=MemoryAddressAllocator(); s1=form_site_candidate(road_id='NG-RD-000001',source_reference='17j:c1'); s2=form_site_candidate(road_id='NG-RD-000001',source_reference='17j:c2')
    a.reserve_specific(series,site_id=s1.site_id,display_number='14',idempotency_key='c1')
    try: a.reserve_specific(series,site_id=s2.site_id,display_number='14',idempotency_key='c2')
    except AddressNumberCollisionError: return True
    return False


def different_scope_visible_number_contract():
    a=MemoryAddressAllocator()
    sa=AddressSeriesDefinition('addrseries:nngla:17j-scope-a','NG-RD-000001','','SEQUENTIAL','ROAD','scope:a',1,1,'INTEGER','NONE',False)
    sb=AddressSeriesDefinition('addrseries:nngla:17j-scope-b','NG-RD-000001','','SEQUENTIAL','ROAD','scope:b',1,1,'INTEGER','NONE',False)
    s1=form_site_candidate(road_id='NG-RD-000001',source_reference='17j:scope:a'); s2=form_site_candidate(road_id='NG-RD-000001',source_reference='17j:scope:b')
    r1=a.reserve_specific(sa,site_id=s1.site_id,display_number='14',idempotency_key='a'); r2=a.reserve_specific(sb,site_id=s2.site_id,display_number='14',idempotency_key='b')
    return r1.display_address_number==r2.display_address_number=='14' and r1.series_id!=r2.series_id

def recovery_rows():
    return (
      RecoveryResult('sequence-gap-after-rollback','IMMUTABLE_ID',True,False,False,False,True,'PASS'),
      RecoveryResult('retry-after-commit','ADDRESS',True,True,False,idempotent_address_replay(),True,'PASS'),
    )
__all__=['idempotent_address_replay','collision_contract','different_scope_visible_number_contract','recovery_rows']
