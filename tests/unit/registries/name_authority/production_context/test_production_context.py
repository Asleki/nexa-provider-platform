import pytest
from registries.reference_authority import *
from registries.name_authority.production_context import *

def refs():
    r=MemoryReferenceRepository()
    r.add(ReferenceRecord('tribe:1','trb_001','tribe','Vondoria',created_by_actor_id='a',approved_by_actor_id='b'))
    r.add(ReferenceRecord('language:1','lng_001','language','Spanish',created_by_actor_id='a',approved_by_actor_id='b'))
    r.add(ReferenceRecord('origin:1','org_001','origin','Spain',origin_type='country',created_by_actor_id='a',approved_by_actor_id='b'))
    return r

def test_accented_compound_profile_preserves_unicode_and_tokens():
    p=NameOrthographyProfile('p','n','production','compound_space_separated','García Hernández','a','b')
    assert p.accented is True and p.tokens==('García','Hernández') and p.token_count==2

def test_dangerous_forms_remain_distinct():
    assert NameOrthographyProfile('1','n1','production','simple','Peña','a','b').canonical_value_snapshot!='Pena'
    assert NameOrthographyProfile('2','n2','production','joined_prefix','McDonald','a','b').canonical_value_snapshot!='Mc Donald'

def test_native_surname_requires_tribe():
    with pytest.raises(ValueError): ProductionNameContextPolicy().validate(NameProductionContextRequest('n','production','surname','native','simple','Bregach','a','b'))

def test_foreign_surname_requires_origin_and_language():
    with pytest.raises(ValueError): ProductionNameContextPolicy().validate(NameProductionContextRequest('n','production','surname','foreign','simple','Peña','a','b',origin_reference_id='origin:1'))

def test_service_creates_resolved_context_and_readiness():
    c=MemoryNameContextRepository(); s=NameProductionContextService(c,refs())
    req=NameProductionContextRequest('n','production','surname','foreign','compound_space_separated','García Hernández','a','b','language:1','origin:1')
    p,rel=s.apply(req)
    assert p.accented is True and len(rel)==2 and s.readiness('n') is True

def test_cross_runtime_reference_rejected():
    r=refs(); r.add(ReferenceRecord('language:sim','lng_002','language','X','simulation',created_by_actor_id='a',approved_by_actor_id='b'))
    with pytest.raises(ValueError): NameProductionContextService(MemoryNameContextRepository(),r).apply(NameProductionContextRequest('n','production','first_name','foreign','simple','X','a','b',language_reference_id='language:sim'))
