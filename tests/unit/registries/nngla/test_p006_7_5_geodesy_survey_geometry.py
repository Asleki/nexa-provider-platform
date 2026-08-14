import pytest
from registries.country.operating_context import RecordEffectScope
from registries.nngla.bundle15b_source import load_crs_definitions,load_geometry_types,load_survey_accuracy_classes,load_geometry_versions,load_survey_control_points
from registries.nngla.geometry_versions import GeometryAuthorityLevel,GeometryPublicationStatus,MemoryGeometryAuthorityRepository
from registries.nngla.survey import SurveyRecord,MemorySurveyRepository

def test_governed_crs_and_geometry_vocabulary_are_complete():
    crs=load_crs_definitions(); types=load_geometry_types()
    assert len(crs)==1 and crs[0].crs_code=='NG-CRS-EPSG4326' and crs[0].axis_order=='LONGITUDE_LATITUDE'
    assert {x.geometry_type_code for x in types}=={'POINT','MULTIPOINT','LINESTRING','MULTILINESTRING','POLYGON','MULTIPOLYGON'}

def test_geometry_candidates_preserve_authority_and_source_distinction():
    rows=load_geometry_versions(); repo=MemoryGeometryAuthorityRepository()
    assert len(rows)==21
    for r in rows: repo.add(r)
    authoritative=[r for r in rows if r.authoritative_level is GeometryAuthorityLevel.AUTHORITATIVE]
    assert len(authoritative)==1
    assert authoritative[0].subject_id=='country:novegeo'
    assert authoritative[0].publication_status is GeometryPublicationStatus.PUBLISHED
    assert sum(r.authoritative_level is GeometryAuthorityLevel.QUALIFIED_SOURCE for r in rows)==20
    assert all(r.runtime_effect_scope is RecordEffectScope.SHARED_REFERENCE for r in rows)

def test_geometry_ids_are_stable_while_versions_can_supersede_source_history():
    g=load_geometry_versions()[0]
    assert g.geometry_id=='NG-GEO-000001'
    assert g.supersedes_geometry_id=='boundary:novegeo:sovereign:v001'
    assert g.is_authoritative and g.is_public

def test_survey_accuracy_vocabulary_is_real_and_numeric_tolerances_remain_policy_deferred():
    rows=load_survey_accuracy_classes()
    assert len(rows)==6
    assert {x.accuracy_class_code for x in rows}=={'REFERENCE_ONLY','MAP_APPROXIMATE','GENERAL_SURVEY','CONTROL_SURVEY','CADASTRAL_SURVEY','LEGAL_BOUNDARY'}
    assert all(x.horizontal_accuracy_rule=='PENDING_POLICY' and x.vertical_accuracy_rule=='PENDING_POLICY' for x in rows)
    assert not next(x for x in rows if x.accuracy_class_code=='REFERENCE_ONLY').legal_boundary_eligible

def test_day_zero_survey_control_register_remains_governed_empty_and_survey_identity_is_separate():
    assert load_survey_control_points()==()
    r=SurveyRecord('NG-SRV-000001','CONTROL_SURVEY','evidence:survey:1','instrument:1','approval:1','ACTIVE')
    repo=MemorySurveyRepository(); repo.add(r); assert repo.get('NG-SRV-000001')==r
