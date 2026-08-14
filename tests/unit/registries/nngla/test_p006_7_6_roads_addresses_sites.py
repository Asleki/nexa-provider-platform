import pytest
from registries.country.operating_context import RecordEffectScope
from registries.nngla.bundle15b_source import load_road_classifications,load_road_candidates,load_address_candidates
from registries.nngla.roads import CanonicalRoad,MemoryRoadRepository
from registries.nngla.addressable_sites import AddressableSiteReference,MemoryAddressableSiteRepository
from registries.nngla.addresses import CanonicalAddress,MemoryAddressRepository

def test_complete_governed_road_classification_has_ten_classes():
    classes=load_road_classifications()
    assert len(classes)==10
    assert {x.road_class_code for x in classes}=={'NATIONAL','REGIONAL','DISTRICT','MUNICIPAL','LOCAL','RURAL','ACCESS','SERVICE','UNCLASSIFIED','PRIVATE_REFERENCE'}

def test_road_source_preserves_all_900_reserved_unmapped_references():
    roads=load_road_candidates(); assert len(roads)==900
    assert all(r.planning_status=='RESERVED_REFERENCE' for r in roads)
    assert all(r.geometry_status=='UNMAPPED_PENDING_CONSTRUCTION_OR_SURVEY' and r.geometry_reference is None for r in roads)
    assert all(r.runtime_effect_scope is RecordEffectScope.SHARED_REFERENCE for r in roads)
    assert all(r.addressing_eligible for r in roads)

def test_road_candidate_name_and_canonical_road_identities_remain_distinct():
    src=load_road_candidates()[0]
    road=CanonicalRoad('NG-RD-000001',src.road_candidate_id,src.road_name_id,src.road_class_code,None,'RESERVED',RecordEffectScope.SHARED_REFERENCE)
    assert len({road.road_id,road.source_candidate_id,road.road_name_id})==3
    repo=MemoryRoadRepository(); repo.add(road); assert repo.get(road.road_id)==road

def test_addressable_site_is_not_parcel_building_or_address_identity():
    site=AddressableSiteReference('site:novegeo:000001','NGP-000001',None,'NG-RD-000001',None,None,'RESERVED',RecordEffectScope.SHARED_REFERENCE)
    repo=MemoryAddressableSiteRepository(); repo.add(site); assert repo.get(site.site_id)==site
    address=CanonicalAddress('NG-ADR-000001',site.site_id,'NG-RD-000001','12',None,'ACTIVE',RecordEffectScope.SHARED_REFERENCE)
    arepo=MemoryAddressRepository(); arepo.add(address)
    assert address.address_id != site.site_id and arepo.get(address.address_id)==address

def test_address_candidate_register_remains_governed_empty_until_spatial_allocation_exists():
    assert load_address_candidates()==()
