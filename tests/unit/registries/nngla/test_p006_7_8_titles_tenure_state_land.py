from datetime import date
import pytest
from registries.country.operating_context import RecordEffectScope
from registries.nngla.bundle15c_source import load_tenure_types,load_title_types,load_state_land_categories,load_title_bootstrap,load_state_land_bootstrap
from registries.nngla.titles import TitleRecord,TitleStatus,MemoryTitleRepository
from registries.nngla.state_land import StateLandRecord,MemoryStateLandRepository

def test_complete_governed_tenure_and_title_vocabularies_preserve_joint_and_limited_semantics():
    tenures=load_tenure_types(); types=load_title_types()
    assert len(tenures)==7 and len(types)==6
    assert {x.tenure_type_code for x in tenures}=={'FREEHOLD','LEASEHOLD','STATE','PUBLIC','COMMUNAL','CUSTOMARY','JOINT'}
    assert {x.title_type_code for x in types}=={'FREEHOLD_TITLE','LEASEHOLD_TITLE','STATE_LEASE','COMMUNAL_HOLDING','CUSTOMARY_HOLDING','JOINT_TITLE'}
    assert any(x.transferable=='limited' for x in tenures)
    assert any(x.transferable=='limited' for x in types)

def test_title_is_distinct_from_parcel_tenure_and_holder_reference():
    t=TitleRecord('NG-TTL-000001','NV-12-004-8890','FREEHOLD_TITLE','FREEHOLD','citizen:novegeo:000001',TitleStatus.ACTIVE,date(2026,8,14),None,'test:title')
    assert len({t.title_id,t.parcel_id,t.holder_reference})==3
    assert t.runtime_effect_scope is RecordEffectScope.RUNTIME_SCOPED
    repo=MemoryTitleRepository(); repo.add(t); assert repo.for_parcel(t.parcel_id)==(t,)

def test_title_effective_dating_and_holder_reference_are_governed_without_embedding_holder_data():
    with pytest.raises(ValueError): TitleRecord('NG-TTL-000001','NV-12-004-8890','FREEHOLD_TITLE','FREEHOLD','Alex Malunda',TitleStatus.ACTIVE,date(2026,8,14),None,'bad:embedded-name')
    with pytest.raises(ValueError): TitleRecord('NG-TTL-000001','NV-12-004-8890','FREEHOLD_TITLE','FREEHOLD','citizen:novegeo:000001',TitleStatus.ACTIVE,date(2026,8,15),date(2026,8,14),'bad:date')

def test_state_land_is_a_separate_effective_dated_record_over_a_parcel_and_namespace_remains_opaque():
    categories=load_state_land_categories(); assert len(categories)==6
    assert {x.state_land_category_code for x in categories}=={'GENERAL_STATE_LAND','PUBLIC_RESERVE','INFRASTRUCTURE_RESERVE','CONSERVATION_RESERVE','ADMINISTRATIVE_LAND','FUTURE_ALLOCATION'}
    r=StateLandRecord('state-land:novegeo:000001','NV-12-004-8890','GENERAL_STATE_LAND','NG-ADM-CAND-000001','ACTIVE',date(2026,8,14),None,'test:state')
    repo=MemoryStateLandRepository(); repo.add(r); assert repo.for_parcel(r.parcel_id)==(r,)
    assert r.runtime_effect_scope is RecordEffectScope.RUNTIME_SCOPED

def test_day_zero_title_and_state_land_registers_remain_real_governed_empty_registers():
    assert load_title_bootstrap()==()
    assert load_state_land_bootstrap()==()
