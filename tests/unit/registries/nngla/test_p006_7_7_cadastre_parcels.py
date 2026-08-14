from datetime import date
import pytest
from registries.country.operating_context import RecordEffectScope
from registries.nngla.bundle15c_source import load_land_use_codes,load_parcel_bootstrap
from registries.nngla.parcels import ParcelRecord,ParcelStatus,MemoryParcelRepository
from registries.nngla.parcel_lineage import ParcelLineageAction,ParcelLineageRecord,MemoryParcelLineageRepository
from registries.nngla.cadastre import CadastralGeometryAssociation

def _parcel(pid='NV-12-004-8890',parent=None,status=ParcelStatus.ACTIVE,geometry='NG-GEO-000123'):
    return ParcelRecord(pid,parent,'SERIES-A','8890',status,geometry,'AGRICULTURAL','SURVEYED',date(2026,8,14),None,'test:parcel')

def test_complete_governed_land_use_vocabulary_has_thirteen_legal_classes():
    items=load_land_use_codes()
    assert len(items)==13
    assert {x.land_use_code for x in items}=={'RESIDENTIAL','COMMERCIAL','INDUSTRIAL','AGRICULTURAL','INSTITUTIONAL','TRANSPORT','UTILITY','CONSERVATION','FORESTRY','RECREATION','WATER','UNCLASSIFIED','MIXED_USE'}
    assert all(x.legal_classification for x in items)

def test_parcel_identity_geometry_and_status_are_separate_contracts():
    p=_parcel()
    assert p.parcel_id=='NV-12-004-8890'
    assert p.geometry_reference=='NG-GEO-000123'
    assert p.parcel_status is ParcelStatus.ACTIVE
    assert p.runtime_effect_scope is RecordEffectScope.RUNTIME_SCOPED
    repo=MemoryParcelRepository(); repo.add(p); assert repo.get(p.parcel_id)==p

def test_parcel_rejects_self_parent_and_geometry_identity_must_not_replace_parcel_identity():
    with pytest.raises(ValueError): _parcel(parent='NV-12-004-8890')
    with pytest.raises(ValueError): _parcel(geometry='NV-12-004-8890')

def test_subdivision_and_consolidation_preserve_predecessor_successor_lineage():
    sub=ParcelLineageRecord('parcel-lineage:000001',ParcelLineageAction.SUBDIVISION,('NV-12-004-8890',),('NV-12-004-8891','NV-12-004-8892'),date(2026,8,14),'test:subdivision')
    con=ParcelLineageRecord('parcel-lineage:000002',ParcelLineageAction.CONSOLIDATION,('NV-12-004-8891','NV-12-004-8892'),('NV-12-004-9000',),date(2026,8,15),'test:consolidation')
    repo=MemoryParcelLineageRepository(); repo.add(sub); repo.add(con)
    assert repo.involving('NV-12-004-8891')==(sub,con)
    with pytest.raises(ValueError): ParcelLineageRecord('parcel-lineage:bad',ParcelLineageAction.SUBDIVISION,('NV-12-004-8890',),('NV-12-004-8890','NV-12-004-8891'),date(2026,8,14),'bad')

def test_cadastral_geometry_reuses_bundle15b_geometry_and_survey_identities_while_day_zero_parcels_stay_empty():
    a=CadastralGeometryAssociation('NV-12-004-8890','NG-GEO-000123','NG-SRV-000001','CADASTRAL_BOUNDARY',date(2026,8,14),None,'test:survey')
    assert a.parcel_id!='NG-GEO-000123' and a.geometry_id=='NG-GEO-000123'
    assert load_parcel_bootstrap()==()
